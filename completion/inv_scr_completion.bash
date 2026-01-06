#!/bin/bash
# Bash completion script for inv_scr CLI
# Install this by sourcing it in your .bashrc or .bash_profile:
#   source /path/to/inv_scr_completion.bash
# Or copy to /etc/bash_completion.d/ or /usr/local/etc/bash_completion.d/

_inv_scr_completion() {
    local cur prev opts operations
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Available operations
    operations="azs cfnstacks cfnstacksets cloudtrail config-recorders directories ebs-volumes ecs-clusters elbs enis functions gas gd-detectors instances list org-users orgs phzs policies ram-shares rds-instances roles saml-providers subnets tgws topics vpcs"
    
    # Common options
    common_opts="--profiles --regions --role-to-use --root-only --save-to-file --timing --verbose --quiet --version --help"
    
    case "${prev}" in
        inv_scr)
            COMPREPLY=( $(compgen -W "${operations}" -- ${cur}) )
            return 0
            ;;
        --profiles)
            # Complete AWS profiles from ~/.aws/config
            if [[ -f ~/.aws/config ]]; then
                local profiles=$(grep '^\[profile ' ~/.aws/config | sed 's/\[profile \(.*\)\]/\1/')
                COMPREPLY=( $(compgen -W "${profiles}" -- ${cur}) )
            fi
            return 0
            ;;
        --regions)
            # Complete AWS regions
            local regions="us-east-1 us-east-2 us-west-1 us-west-2 eu-west-1 eu-west-2 eu-central-1 ap-southeast-1 ap-southeast-2 ap-northeast-1 all"
            COMPREPLY=( $(compgen -W "${regions}" -- ${cur}) )
            return 0
            ;;
        --role-to-use)
            # Complete common role names
            local roles="OrganizationAccountAccessRole AWSControlTowerExecution ReadOnlyAccess"
            COMPREPLY=( $(compgen -W "${roles}" -- ${cur}) )
            return 0
            ;;
        --save-to-file)
            # Complete file paths
            COMPREPLY=( $(compgen -f -- ${cur}) )
            return 0
            ;;
        *)
            # Check if we're completing an operation
            if [[ " ${operations} " =~ " ${COMP_WORDS[1]} " ]]; then
                # Complete common options for operations
                COMPREPLY=( $(compgen -W "${common_opts}" -- ${cur}) )
            else
                # Complete operations if no operation selected yet
                COMPREPLY=( $(compgen -W "${operations}" -- ${cur}) )
            fi
            return 0
            ;;
    esac
}

# Register the completion function
complete -F _inv_scr_completion inv_scr