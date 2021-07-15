from panther import lookup_aws_account_name
from panther_base_helpers import deep_get


def rule(event):
    if event.get("eventName") != "ConsoleLogin":
        return False

    additional_event_data = event.get("additionalEventData", {})
    session_context = deep_get(event, "userIdentity", "sessionContext", default={})
    response_elements = event.get("responseElements", {})

    return (
        # Only alert on successful logins
        response_elements.get("ConsoleLogin") == "Success"
        and
        # Where MFA is not in use
        additional_event_data.get("MFAUsed") == "No"
        and
        # Ignoring SSO login events
        not additional_event_data.get("SamlProviderArn")
        and
        # And ignoring logins that were authenticated via a session that was itself
        # authenticated with MFA
        deep_get(session_context, "attributes", "mfaAuthenticated") != "true"
    )


def title(event):
    user_type = deep_get(event, "userIdentity", "type")
    if user_type == "IAMUser":
        user = deep_get(event, "userIdentity", "userName")
    # root user
    elif user_type == "Root":
        user = user_type
    else:
        user = "<UNKNOWN_USER>"
    return (
        "AWS login detected without MFA for user "
        f"[{user}] "
        "in account "
        f"[{lookup_aws_account_name(event.get('recipientAccountId'))}]"
    )
