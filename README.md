Keyhook
=======

Keyhook is a kubernetes validating admission webhook for managing kubernetes
resource quotas in conjunction with the Hierarchical Namespace Controller.

This is very experimental. Currently the only resource that can be managed is
the number of pods that may be created.

Usage
-----

Run keystone in devstack. In /etc/keystone/keystone.conf, create a new section
`[unified_limit]` and add the config option `enforcement_model =
strict_two_level` and restart keystone.

Create a service and endpoint for kubernetes:

```
$ openstack service create kubernetes --name kubernetes
+---------+----------------------------------+
| Field   | Value                            |
+---------+----------------------------------+
| enabled | True                             |
| id      | 2db1c2fe81d045108cd0ba63a72960cd |
| name    |                                  |
| type    | kubernetes                       |
+---------+----------------------------------+
$ openstack endpoint create kubernetes public https://192.168.122.79:6443 --region RegionOne
+--------------+----------------------------------+
| Field        | Value                            |
+--------------+----------------------------------+
| enabled      | True                             |
| id           | a97f4b315162409f8fcbef797777ec99 |
| interface    | public                           |
| region       | RegionOne                        |
| region_id    | RegionOne                        |
| service_id   | 2db1c2fe81d045108cd0ba63a72960cd |
| service_name | kubernetes                       |
| service_type | kubernetes                       |
| url          | https://192.168.122.79:6443      |
+--------------+----------------------------------+
```

Create a domain and subprojects:

```
$ openstack --os-cloud=devstack-system-admin domain create org1
+-------------+----------------------------------+
| Field       | Value                            |
+-------------+----------------------------------+
| description |                                  |
| enabled     | True                             |
| id          | 511b180417954e29bb03212a177f58bd |
| name        | org1                             |
| options     | {}                               |
| tags        | []                               |
+-------------+----------------------------------+
$ openstack --os-cloud=devstack-system-admin project create team-a --domain org1
+-------------+----------------------------------+
| Field       | Value                            |
+-------------+----------------------------------+
| description |                                  |
| domain_id   | 511b180417954e29bb03212a177f58bd |
| enabled     | True                             |
| id          | c8364aeb843c485cab13a3ff77e3f4e5 |
| is_domain   | False                            |
| name        | team-a                           |
| options     | {}                               |
| parent_id   | 511b180417954e29bb03212a177f58bd |
| tags        | []                               |
+-------------+----------------------------------+
$ openstack --os-cloud=devstack-system-admin project create team-b --domain org1
+-------------+----------------------------------+
| Field       | Value                            |
+-------------+----------------------------------+
| description |                                  |
| domain_id   | 511b180417954e29bb03212a177f58bd |
| enabled     | True                             |
| id          | dbee308b3eb54da991ff53f61034e6b9 |
| is_domain   | False                            |
| name        | team-b                           |
| options     | {}                               |
| parent_id   | 511b180417954e29bb03212a177f58bd |
| tags        | []                               |
+-------------+----------------------------------+
```

Create corresponding namespaces in kubernetes - right now you have to use the
project ID as the namespace name:

```
$ kubectl create ns 511b180417954e29bb03212a177f58bd
namespace/511b180417954e29bb03212a177f58bd created
$ kubectl hns --kubeconfig admin.conf create c8364aeb843c485cab13a3ff77e3f4e5 -n 511b180417954e29bb03212a177f58bd
Adding required child (subnamespace) c8364aeb843c485cab13a3ff77e3f4e5 to 511b180417954e29bb03212a177f58bd
Succesfully updated 1 property of the hierarchical configuration of 511b180417954e29bb03212a177f58bd
$ kubectl hns --kubeconfig admin.conf create dbee308b3eb54da991ff53f61034e6b9 -n 511b180417954e29bb03212a177f58bd
Adding required child (subnamespace) dbee308b3eb54da991ff53f61034e6b9 to 511b180417954e29bb03212a177f58bd
$ kubectl hns tree 511b180417954e29bb03212a177f58bd
511b180417954e29bb03212a177f58bd
├── c8364aeb843c485cab13a3ff77e3f4e5
└── dbee308b3eb54da991ff53f61034e6b9
```

Now create limits in keystone. First create the registered limit, which will be
the default resource limit for all projects:

```
$ openstack registered limit create --service kubernetes --region RegionOne --default-limit 10 pods
+---------------+----------------------------------+
| Field         | Value                            |
+---------------+----------------------------------+
| default_limit | 10                               |
| description   | None                             |
| id            | 198a7f063448462b99eec43c2d718864 |
| region_id     | RegionOne                        |
| resource_name | pods                             |
| service_id    | 2db1c2fe81d045108cd0ba63a72960cd |
+---------------+----------------------------------+
```

Now create project limits:

```
$ openstack limit create --project 511b180417954e29bb03212a177f58bd --service kubernetes --resource-limit 10 --region RegionOne pods
+----------------+----------------------------------+
| Field          | Value                            |
+----------------+----------------------------------+
| description    | None                             |
| domain_id      | 511b180417954e29bb03212a177f58bd |
| id             | f1aebd7e72ce4c20a0934d18c629bcff |
| project_id     | None                             |
| region_id      | RegionOne                        |
| resource_limit | 10                               |
| resource_name  | pods                             |
| service_id     | 2db1c2fe81d045108cd0ba63a72960cd |
+----------------+----------------------------------+
$ openstack limit create --project c8364aeb843c485cab13a3ff77e3f4e5 --service kubernetes --resource-limit 5 --region RegionOne pods
+----------------+----------------------------------+
| Field          | Value                            |
+----------------+----------------------------------+
| description    | None                             |
| domain_id      | None                             |
| id             | 8dd5be6dfe6e40e18ea9aea15ced7232 |
| project_id     | c8364aeb843c485cab13a3ff77e3f4e5 |
| region_id      | RegionOne                        |
| resource_limit | 5                                |
| resource_name  | pods                             |
| service_id     | 2db1c2fe81d045108cd0ba63a72960cd |
+----------------+----------------------------------+
$ openstack limit create --project dbee308b3eb54da991ff53f61034e6b9 --service kubernetes --resource-limit 5 --region RegionOne pods
+----------------+----------------------------------+
| Field          | Value                            |
+----------------+----------------------------------+
| description    | None                             |
| domain_id      | None                             |
| id             | 027382b0b28c4fb084a8dc190a26c257 |
| project_id     | dbee308b3eb54da991ff53f61034e6b9 |
| region_id      | RegionOne                        |
| resource_limit | 5                                |
| resource_name  | pods                             |
| service_id     | 2db1c2fe81d045108cd0ba63a72960cd |
+----------------+----------------------------------+
```

Create a self-signed key pair named cert.pem and key.pem in the current working
directory, and add a kubeconfig.conf file that the webhook can use to
authenticate to the kubernetes API server. Also create a
~/.config/openstack/clouds.yaml that your user can use to access your keystone
server. Then run the webhook server:

```
$ tox -evenv -- python3 hook.py
GLOB sdist-make: /home/colleen/dev/webhook/setup.py
venv inst-nodeps: /home/colleen/dev/webhook/.tox/.tmp/package/1/keystone-hook-0.0.1.zip
venv installed: appdirs==1.4.3,Babel==2.8.0,cachetools==4.0.0,certifi==2019.11.28,cffi==1.14.0,chardet==3.0.4,cryptography==2.8,debtcollector==2.0.0,decorator==4.4.1,dogpile.cache==0.9.0,entrypoints==0.3,flake8==3.7.9,google-auth==1.11.1,idna==2.8,iso8601==0.1.12,jmespath==0.9.4,jsonpatch==1.25,jsonpointer==2.0,keystone-hook==0.0.1,keystoneauth1==3.18.0,kubernetes==10.0.1,mccabe==0.6.1,msgpack==0.6.2,munch==2.5.0,netaddr==0.7.19,netifaces==0.10.9,oauthlib==3.1.0,openstacksdk==0.41.0,os-service-types==1.7.0,oslo.config==8.0.0,oslo.context==3.0.0,oslo.i18n==4.0.0,-e git+https://opendev.org/openstack/oslo.limit@0a54c217286ec26b18d97a554c0b0104142992c8#egg=oslo.limit,oslo.log==4.0.0,oslo.serialization==3.0.0,oslo.utils==4.0.0,pbr==5.4.4,pyasn1==0.4.8,pyasn1-modules==0.2.8,pycodestyle==2.5.0,pycparser==2.19,pyflakes==2.1.1,pyinotify==0.9.6,pyparsing==2.4.6,python-dateutil==2.8.1,pytz==2019.3,PyYAML==5.3,requests==2.22.0,requests-oauthlib==1.3.0,requestsexceptions==1.4.0,rfc3986==1.3.2,rsa==4.0,six==1.14.0,stevedore==1.32.0,urllib3==1.25.8,websocket-client==0.57.0,wrapt==1.11.2
venv run-test-pre: PYTHONHASHSEED='83833320'
venv run-test: commands[0] | python3 hook.py
Starting webhook server...
```

Ensure that the kubernetes API server can access the webhook by resolving the
hostname hello.world.hook. Replace the caBundle setting in webhook.yaml with the
contents of the cert.pem that you generated. Create the webhook configuration in
kubernetes:

```
$ kubectl apply -f webhook.yaml
validatingwebhookconfiguration.admissionregistration.k8s.io/hello-world created
```

Try creating deployments in each of the namespaces with different numbers of
replicas. With a resource limit of 10 for the entire tree, consuming 5 pods in
the namespace for team-a means that the namespace for org1 should not be able to
claim 6 pods, etc. For example, use all the quota for one of the children:

$ kubectl -n c8364aeb843c485cab13a3ff77e3f4e5 get deployment
NAME               READY   UP-TO-DATE   AVAILABLE   AGE
nginx-deployment   5/5     5            5           63m

With normal quota management, the parent and siblings of the namespace would be
independent of the resource usage of another namespace. With hierarchical quota
management, even though the limit for the parent namespace is 10, if we try to
use 6 resources that brings the total over the limit for the tree:

$ kubectl -n 511b180417954e29bb03212a177f58bd get deployment
NAME               READY   UP-TO-DATE   AVAILABLE   AGE
nginx-deployment   5/6     5            5           19s

Once we reduce the child to a lower usage...:

$ kubectl -n c8364aeb843c485cab13a3ff77e3f4e5 get deployment
NAME               READY   UP-TO-DATE   AVAILABLE   AGE
nginx-deployment   3/3     3            3           63m

...then the parent can claim the rest of its requested resources:

$ kubectl -n 511b180417954e29bb03212a177f58bd get deployment
NAME               READY   UP-TO-DATE   AVAILABLE   AGE
nginx-deployment   6/6     6            6           62s
