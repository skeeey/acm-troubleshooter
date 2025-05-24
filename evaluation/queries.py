# coding: utf-8

# pylint: disable=line-too-long

"""
The cases for index evaluation
"""

queries = [
'''troubleshoot why the status of my cluster cluster-a is unknown''',
'''troubleshoot why my addons are missing in my cluster cluster-b''',
'''tell me what is ACM?''',
'''the work-manager addon is not installed in the local-cluster''',
'''how to configure klusterletaddonconfig ?''',
'''Can I use addonDeploymentConfig to configure http proxy for an addon?''',
'''How can I Configure nodeSelectors and tolerations for klusterlet add-ons?''',
'''Cluster can not be imported into ACM, when the HCP being imported is on the same HOSTING cluster as the ACM which is running in an HCP''',
'''Can I rename the local-cluster?''',
'''what values can I configure for mce AvailabilityConfig?''',
'''what's the acm?''',
'''Some AppliedManifestWork got left behind after detaching the spoke. why?''',
'''I am using a downstream build ACM, and I want to import a KinD cluster, but my importing failed as ImagePullBackOff, how can I do to fix that?''',
'''I found the following error in the log of klusterlet on one of my managed cluster. How can I fix it?
"KlusterletController" controller failed to sync "klusterlet", err: "klusterlet/managed/klusterlet-work-clusterrolebinding.yaml" (string): ClusterRoleBinding.rbac.authorization.k8s.io "open-cluster-management:klusterlet-work:agent" is invalid: roleRef: Invalid value: rbac.RoleRef{APIGroup:"rbac.authorization.k8s.io", Kind:"ClusterRole", Name:"open-cluster-management:klusterlet-work:agent"}: cannot change roleRef
''',
'''why my addons are missing in my cluster?''',
'''tell me what is ACM?''',
'''The iam-policy-controller does not get removed when I upgraded to ACM 2.11, what is the fix?''',
'''On ACM hub showing wrong command for importing managed cluster, error "error: no objects passed to create The cluster cannot be imported because its Klusterlet CRD already exists."
Description of problem
On ACM hub showing wrong command for importing managed cluster, error "error: no objects passed to create The cluster cannot be imported because its Klusterlet CRD already exists."

Version-Release number of selected component (if applicable): 2.13
How reproducible:
Steps to Reproduce:
Create ACM hub on 3 node OCP 4.18 BM cluster.
Follow below steps on above ACM hub
Step 1:  Install Advanced Cluster Management from OperatorHub with the default values.
https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.13/html-single/install/index#installing-[…]operatorhub
Step 2: Prepare ACM to import the clusters where MultiCluster Engine is present.
https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kub[…]ngine_operator_with_red_hat_advanced_cluster_management/index
Main sections:
1.1.2.1. Configuring add-ons
1.1.2.2. Creating a KlusterletConfig resource
After that run https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.13/html-single/multicluster_engine_operator_with_red_hat_advanced_cluster_management/index#hosted-import-mce
Follow from step 1 till step "Run oc apply -f <filename>.yaml to apply the file."

After that on ACM hub GUI OCP it shows "Run this command with kubectl configured for your targeted cluster to start the import"
After you run the command on targeted cluster which we copied from ACM hub GUI its throws below error

error: no objects passed to create
The cluster cannot be imported because its Klusterlet CRD already exists.
Either the cluster was already imported, or it was not detached completely during a previous detach process.
Detach the existing cluster before trying the import again''',
'''How to use addonDeploymentConfig to configure addon?''',
'''how to configure klusterletaddonconfig ?''',
'''How to create ACM cluster? ''',
'''How to disable cluster-proxy add-on?''',
'''team . I have a customer who are creating OCP 4.14 datastore cluster from ACM 2.11 .
Installing datastore clusters are supported from OCP  https://access.redhat.com/solutions/6266251 and https://issues.redhat.com/browse/RFE-3454
but from ACM it fails with :
time="2025-03-24T10:19:04Z" level=fatal msg="failed to fetch Terraform Variables: failed to fetch dependency of \"Terraform Variables\": failed to generate asset \"Platform Provisioning Check\": platform.vsphere.failureDomains.topology.datastore:
Invalid value: \"/VD_VE_VW_O_GRBS_MD3_PRO_001/datastore/VMSAN902_M3_IT4IT_PRO_001\": could not find datastore /VD_VE_VW_O_GRBS_MD3_PRO_001/datastore/VMSAN902_M3_IT4IT_PRO_001"
time="2025-03-24T10:19:05Z" level=error msg="error after waiting for command completion" error="exit status 1" installID=4vt6xdqp

same vmware env used and same ACM with same values , customer can install OCP 4.12 datastore cluster but OCP 4.12 version would not be otherwise supported in ACM 2.11
Despite ACM 2.11 is used installation could not find datastore on OCP 4.14 but it can find if we create OCP 4.12 cluster .
ACM 2.11 is generating an install-config, for vmware with syntax of OCP 4.12 [1] .
sample install-config for 4.12 : https://docs.redhat.com/en/documentation/openshift_container_platform/4.12/html-single/installing_on_vsphere/index#installation-installer-provisioned-vsphere-config-yaml_installing-vsphere-installer-provisioned-customizations
sample install-config for 4.14 : https://docs.redhat.com/en/documentation/openshift_container_platform/4.14/html/installing_on_vsphere/installer-provisioned-infrastructure#installation-installer-provisioned-vsphere-config-yaml_installing-vsphere-installer-provisioned-customizations
install configs and logs customer used is at https://access.redhat.com/support/cases/04096137
Customer upgraded ACM from 2.10 to 2.11 . I have checked in must-gather if any MCE , ACM versions mismatch , but I all seems good
      installer.open-cluster-management.io/release-version: 2.11.6
      installer.multicluster.openshift.io/release-version: 2.6.6
      installer.open-cluster-management.io/release-version: 2.11.6
      installer.open-cluster-management.io/release-version: 2.11.6
      installer.multicluster.openshift.io/release-version: 2.6.6
      installer.open-cluster-management.io/release-version: 2.11.6''',
'''I have a cluster imported with klusterlet Hosted mode, when I detach the cluster, I got :
E0319 12:11:30.667698       1 base_controller.go:266] "KlusterletController" controller failed to sync "klusterlet-29qgdf0br2php6kaop64tljlblijboc6", err: Unauthorized
''',
'''Can I rename the local-cluster?''',
'''Cluster can not be imported into ACM, when the HCP being imported is on the same HOSTING cluster as the ACM which is running in an HCP''',
'''Please help me generate the yaml of policy and necessary resources to add an annotation `immediate-import=true` to all ManagedCluter resoruces on the local-cluster''',
'''ACM 2.11.4 is not getting installed, do we have any known issue?
oc get multiclusterhub -A
NAMESPACE                 NAME              STATUS       AGE
open-cluster-management   multiclusterhub   Installing   28h''',
'''why my addons are missing in my cluster?''',
'''how to use policy to deploy an operator?''',
'''Can I rename the local-cluster to my-test?''',
'''how to deploy an application in ACM console?''',
'''Some AppliedManifestWork got left behind after detaching the spoke. why?''',
'''tell me what is ACM?''',
'''Can I rename the local-cluster?''',
'''what's the acm?''',
'''my globalhub agent did not deploy, could u let me know the possible reasons for this issue?''',
'''I have a rosa hcp cluster, I want to use the discovery feature to auto import this cluster to another ACM? how to do that ?''',
'''How can I deploy a ACM HUB?''',
'''I have a rosa hcp cluster with ACM installed, and I imported another rosa hcp cluster to the hub, but now several addons(not all addons) on the managed cluster crashed with error:
error	certificate-policy-controller	controllers/certificatepolicy_controller.go:102	Failed to list policies	{"error": "failed to get restmapping: failed to get server groups: Get \"https://172.30.0.1:443/api\": context deadline exceeded"}
2025-03-07T21:26:29.339758815Z open-cluster-management.io/cert-policy-controller/controllers.(*CertificatePolicyReconciler).PeriodicallyExecCertificatePolicies
2025-03-07T21:26:29.339758815Z 	/remote-source/cert-policy-controller/app/controllers/certificatepolicy_controller.go:102
2025-03-07T21:26:29.340289397Z 2025-03-07T21:26:29.339Z''',
'''Does anyone know which addon agent code generates this cluster claim from a managed cluster?''',
'''Create an ACM Operator Policy that deploys OpenShift Virtualization Operator
''',
'''We are seeing "unable to get issuer certificate" errors on certain requests from ROSA HCP hub. The certificate errors we have seen occur on requests to the "rbac-query-proxy" & "cluster-proxy-addon-user" Routes. How can I fix it?''',
'''How to use klusterletaddonconfig to configure proxy for an addon?''',
'''Please help me generate the yaml of policy and necessary resources to add an annotation `immediate-import=true` to all ManagedCluter resoruces on the local-cluster''',
'''{"type": "io.open-cluster-management.operator.multiclusterglobalhubs.migration.resources", "error": "admission webhook \"managedclustervalidators.admission.cluster.open-cluster-management.io\" denied the request: managedclusters/accept.cluster.open-cluster-management.io \"mc1\" is forbidden: user \"system:serviceaccount:multicluster-global-hub-agent:multicluster-global-hub-agent\" cannot update the HubAcceptsClient field"}
''',
'''Can I rename the local-cluster?''',
'''tell me what is ACM?''',
'''Some AppliedManifestWork got left behind after detaching the spoke. why?''',
'''How can I deploy an ACM HUB?''',
'''how to configure klusterletaddonconfig ?''',
'''Please provide a policy include an app nginx pod''',
'''I have a rosa hcp cluster with ACM installed, and I imported another rosa hcp cluster to the hub, but now several addons(not all addons) on the managed cluster crashed with error:
error	certificate-policy-controller	controllers/certificatepolicy_controller.go:102	Failed to list policies	{"error": "failed to get restmapping: failed to get server groups: Get \"https://172.30.0.1:443/api\": context deadline exceeded"}
2025-03-07T21:26:29.339758815Z open-cluster-management.io/cert-policy-controller/controllers.(*CertificatePolicyReconciler).PeriodicallyExecCertificatePolicies
2025-03-07T21:26:29.339758815Z 	/remote-source/cert-policy-controller/app/controllers/certificatepolicy_controller.go:102
2025-03-07T21:26:29.340289397Z 2025-03-07T21:26:29.339Z''',
'''what's the acm?''',
'''I have a rosa hcp cluster with ACM installed, and I imported another rosa hcp cluster to the hub, but now several addons(not all addons) on the managed cluster crashed with error:
error	certificate-policy-controller	controllers/certificatepolicy_controller.go:102	Failed to list policies	{"error": "failed to get restmapping: failed to get server groups: Get \"https://172.30.0.1:443/api\": context deadline exceeded"}
2025-03-07T21:26:29.339758815Z open-cluster-management.io/cert-policy-controller/controllers.(*CertificatePolicyReconciler).PeriodicallyExecCertificatePolicies
2025-03-07T21:26:29.339758815Z 	/remote-source/cert-policy-controller/app/controllers/certificatepolicy_controller.go:102
2025-03-07T21:26:29.340289397Z 2025-03-07T21:26:29.339Z''',
'''I have an ACM addon, can I use addonDeploymentConfig to configure HTTP proxy for my addon?''',
'''troubleshoot why my addons are missing in my cluster cluster-b,''',
'''create a policy in default ns, which define two objects: an nginx pod and a service that references it ''',
'''Can I rename the local-cluster?''',
'''How to disable cluster-proxy add-on?''',
'''I am using ACM, I want to import a KinD cluster, but failed to import the cluster because can not pull the image on the KinD cluster.''',
'''How to disable cluster-proxy add-on?''',
'''how to configure klusterletaddonconfig ?''',
'''Can I use addonDeploymentConfig to configure http proxy for an addon?''',
'''I hit an issue where the klusterlet on the managed cluster fails to start due to a missing  PriorityClass  resource. Wondering what the best course of action is?''',
''' troubleshoot why the status of the cluster cluster-a is unknown''',
'''Cluster can not be imported into ACM, when the HCP being imported is on the same HOSTING cluster as the ACM which is running in an HCP''',
'''tell me what is ACM?''',
'''I have a cluster imported with klusterlet Hosted mode, when I detach the cluster, I got :
E0319 12:11:30.667698       1 base_controller.go:266] "KlusterletController" controller failed to sync "klusterlet-29qgdf0br2php6kaop64tljlblijboc6", err: Unauthorized
''',
'''We are seeing "unable to get issuer certificate" errors on certain requests from ROSA HCP hub. The certificate errors we have seen occur on requests to the "rbac-query-proxy" & "cluster-proxy-addon-user" Routes. How can I fix it?''',
'''IHAC who has deployed a cluster using ACM where he wants to enable the multiarc so i have below queries:
1) Do we support multiarch with acm I think yes but just want to confirm?
2) InfraEnv should be created in same namespace where the cluster is or it can be anywhere, doesn’t matter?
Any insights on this would be very helpful. Thank you.''',
'''I have a rosa hcp cluster with ACM installed, and I imported another rosa hcp cluster to the hub, but now several addons(not all addons) on the managed cluster crashed with error:
error	certificate-policy-controller	controllers/certificatepolicy_controller.go:102	Failed to list policies	{"error": "failed to get restmapping: failed to get server groups: Get \"https://172.30.0.1:443/api\": context deadline exceeded"}
2025-03-07T21:26:29.339758815Z open-cluster-management.io/cert-policy-controller/controllers.(*CertificatePolicyReconciler).PeriodicallyExecCertificatePolicies
2025-03-07T21:26:29.339758815Z 	/remote-source/cert-policy-controller/app/controllers/certificatepolicy_controller.go:102
2025-03-07T21:26:29.340289397Z 2025-03-07T21:26:29.339Z''',
'''How to pause MCH?''',
'''I can create custom butane/machineconfig manifests to feed to openshift-install agent create image but how can I provide such manifests to MCE?''',
'''my globalhub agent did not deploy, could u let me know the possible reasons for this issue?''',
]
