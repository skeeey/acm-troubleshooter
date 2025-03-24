# coding: utf-8

system_prompt = """
You are a helpful assistant for Red Hat Advanced Cluster Management (ACM) for Kubernetes.
"""

runbook_template = """
Refer to the following dialogue to write a runbooks with the following format:

# <the title of the problem>

## Symptom:
<the problem symptom description>

## Identifying the problem:
<describing how to identify the problem>

## Resolving the problem:
<describing how to resolve the problem>

Dialogue:
{dialogue}
"""

squad_template = """
Find suitable squads from the following list to assign the given issue and output the squads with JSON.

- acm-hub-installer: maintains ACM operator, user install and subscribe to ACM through Operator Lifecycle Manager (OLM),
  which manages the installation, upgrade, and removal of the components that encompass the ACM hub cluster.
  Because ACM depends on and uses the multicluster engine operator, after you create the MultiClusterHub resource during
  installation, the ACM operator automatically installs the multicluster engine operator and creates the 
  MultiClusterEngine resource.
- acm-console: maintains the ACM console which provides comprehensive tools for managing and monitoring
  multiple Kubernetes clusters. Key features include an integrated search functionality for quickly
  finding resources, virtual machine operations for managing VMs directly from the console, and a
  multi-cluster management view that offers detailed insights into cluster health, compliance, and
  application deployments. The console also supports API exploration and managed cluster addon management, 
  enabling users to streamline complex operations and enhance productivity with a user-friendly interface.
- ocp-assisted-installer: focuses on developing a user-friendly OpenShift installation solution,
  primarily for bare metal. They maintain two key components: the OpenShift Assisted Service,
  which hosts installation artifacts (Ignition files, installation configuration, discovery ISO) and
  provides UI/REST API access, and the OpenShift Assisted Installer, which simplifies cluster 
  installation via a web interface and supports Single Node OpenShift (SNO) deployments.
- hypershift: maintains HyperShift component which is middleware for hosting OpenShift control planes
  (Hosted control planes, HCP) at scale that solves for cost and time to provision, as well as portability cross cloud with strong
  separation of concerns between management and workloads. Hosted clusters are fully compliant OpenShift
  Container Platform (OCP) clusters and are compatible with standard OCP and Kubernetes toolchains. 

Output example:
{{"squads":["hypershift", "acm-hub-installer"]}}

Issue:
{issue}
"""
