#!/usr/bin/env bash

####################################
# Convert ACM docs from .adoc to .md
#################################### 

convert() {
    local root_dir="$1"
    local current_file="$2"
    local out_dir="$3"
    if [[ "$current_file" == $root_dir* ]]; then
       modified_path="${current_file#$root_dir/}"
       echo "$out_dir/$modified_path.md"
       npx downdoc -a acm="Red Hat Advanced Cluster Management for Kubernetes" \
            -a acm-short="Red Hat Advanced Cluster Management" \
            -a addons="klusterlet add-ons" \
            -a aap="Red Hat Ansible Automation Platform" \
            -a aap-short="Ansible Automation Platform" \
            -a assist-install="Infrastructure Operator for Red Hat OpenShift" \
            -a cincinnati="Red Hat OpenShift Update Service" \
            -a cincinnati-short="OpenShift Update Service" \
            -a global-hub="multicluster global hub" \
            -a mce="multicluster engine for Kubernetes operator" \
            -a mce-short="multicluster engine operator" \
            -a ocp="Red Hat OpenShift Container Platform" \
            -a ocp-short="OpenShift Container Platform" \
            -a ocp-virt="Red Hat OpenShift Virtualization" \
            -a ocp-virt-short="OpenShift Virtualization"  \
            -a olm="Operator Lifecycle Manager" \
            -a ocm="OpenShift Cluster Manager" \
            -a rosa="OpenShift Service on AWS" \
            -a product-title="Red Hat Advanced Cluster Management for Kubernetes"  \
            -a product-title-short="Red Hat Advanced Cluster Management"  \
            -a product-version="2.12" \
            -a mce-version="2.7" \
            -a product-version-prev="2.11" \
            -a quay="Red Hat Quay" \
            -a quay-short="Quay" \
            -a imagesdir="../images" \
            -a sno="single-node OpenShift" \
            -a support-matrix="https://access.redhat.com/articles/7055998" \
            -a support-matrix-mce="https://access.redhat.com/articles/7056007" \
            -o $out_dir/"$modified_path.md" $current_file
    fi
}

make_out_dir() {
    local root_dir="$1"
    local current_dir="$2"
    local out_dir="$3"
    if [[ "$current_dir" == $root_dir* ]]; then
       modified_path="${current_dir#$root_dir/}"
       mkdir -p $out_dir/$modified_path
    fi
}

# Function to traverse directories
traverse_dir() {
    local root_dir="$1"
    local current_dir="$2"
    local out_dir="$3"
    
    # List all files and directories in the current directory
    for entry in "$current_dir"/*; do
        if [ -d "$entry" ]; then
            if [ "$(basename "$entry")" == "modules" ]; then
                continue
            fi
            if [ "$(basename "$entry")" == ".github" ]; then
                continue
            fi
            if [ "$(basename "$entry")" == ".vscode" ]; then
                continue
            fi
            if [ "$(basename "$entry")" == "apis" ]; then
                continue
            fi
            if [ "$(basename "$entry")" == "api" ]; then
                continue
            fi
            if [ "$(basename "$entry")" == "images" ]; then
                continue
            fi
            make_out_dir "$root_dir" "$entry" "$out_dir"
            traverse_dir "$root_dir" "$entry" "$out_dir"
        elif [ -f "$entry" ] && [[ "$entry" == *.adoc ]]; then
            if [ "$(basename "$entry")" == "main.adoc" ]; then
                continue
            fi
            if [ "$(basename "$entry")" == "master.adoc" ]; then
                continue
            fi
            if [ "$(basename "$entry")" == ".asciidoctorconfig.adoc" ]; then
                continue
            fi
            if [ "$(basename "$entry")" == "EXTERNAL_CONTRIBUTING.adoc" ]; then
                continue
            fi
            if [ "$(basename "$entry")" == "README.adoc" ]; then
                continue
            fi
            if [ "$(basename "$entry")" == "SECURITY.adoc" ]; then
                continue
            fi
            
            convert "$root_dir" "$entry" "$out_dir"
        fi
    done
}

# Check if a directory was provided as an argument
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <adoc directory> <output directory>"
    exit 1
fi

# Install downdoc
npm i downdoc

mkdir -p $2
# Start traversing from the provided directory
traverse_dir "$1" "$1" "$2"
