import json
import ssl
import http.server

import openstack
from oslo_limit import limit
import oslo_limit.exception
import kubernetes.client


class WebhookHandler(http.server.BaseHTTPRequestHandler):

    openstack_conn = None

    def _setup_openstack_connection(self):
        if not self.openstack_conn:
            self.openstack_conn = openstack.connect(cloud='devstack')
            limit._SDK_CONNECTION = self.openstack_conn.identity

    def _get_kubernetes_data(self, namespace):
        config = kubernetes.config.load_kube_config('kubeconfig.conf')
        api = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(config))
        try:
            pods = api.list_namespaced_pod(namespace)
        except kubernetes.client.rest.ApiException as e:
            self.send_error(500, "Could not get current pods: %s\n" % e)
            return
        return pods.items

    def _usage_callback(self, project_id, resources_to_check):
        return {'pods': len(self._get_kubernetes_data(project_id))}

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        try:
            admissionRequest = json.loads(data)
        except json.decoder.JSONDecodeError:
            self.send_error(400, "Expected JSON")
            return

        try:
            uid = admissionRequest['request']['uid']
            namespace = admissionRequest['request']['namespace']
        except KeyError:
            self.send_error(400, "Invalid AdmissionReview object")
            return

        kind = admissionRequest['request']['kind']['kind']
        if kind == "Pod":
            requested_pods = 1
        else:
            self.send_error(
                400, "Only works for pods")
            return

        print("Incoming request: Kind: %s, Pod Count: %d\n" %
              (kind, requested_pods))

        self._setup_openstack_connection()

        sc = self.openstack_conn.config.get_service_catalog()
        endpoint = sc.endpoint_data_for('kubernetes').endpoint_id
        limit.CONF.oslo_limit.endpoint_id = endpoint
        enforcer = limit.Enforcer(self._usage_callback)

        allowed = True

        project = self.openstack_conn.get_project(namespace)
        if project:
            print("found matching project: %s" % project['id'])
        else:
            try:
                project = self.openstack_conn.get_domain(namespace)
                print("found matching domain: %s" % project['id'])
            except openstack.exceptions.ResourceNotFound:
                print("denying request: no matching project or domain")
                allowed = False

        deltas = {'pods': requested_pods}
        if allowed:
            try:
                enforcer.enforce(project['id'], deltas)
                print("Successfully claimed %d pods" % requested_pods)
            except oslo_limit.exception.ProjectOverLimit:
                allowed = False
                print("Could not claim %d pods" % requested_pods)

        admissionResponse = {
            'apiVersion': 'admission.k8s.io/v1',
            'kind': 'AdmissionReview',
            'response': {
                'uid': uid,
                'allowed': allowed
            }
        }
        httpResponse = json.dumps(admissionResponse)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(httpResponse, 'utf-8'))


def run(handler_class=http.server.BaseHTTPRequestHandler):
    certFile = "cert.pem"
    keyFile = "key.pem"
    httpd = http.server.HTTPServer(("", 8080), handler_class)
    httpd.socket = ssl.wrap_socket(
        httpd.socket, certfile=certFile, keyfile=keyFile, server_side=True)
    print("Starting webhook server...")
    httpd.serve_forever()


if __name__ == '__main__':
    run(handler_class=WebhookHandler)
