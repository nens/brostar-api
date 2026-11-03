"""Resolution of the 'principalInvestigator' KvK number used in corrections.

The BRO does not publish the principalInvestigator in its public responses, so
the number has to come from somewhere else. The organisation of the logged in
user is only used when the request explicitly asks for it.
"""

from typing import Any

from .exceptions import CorrectionValidationError

ORGANISATION_HEADER = "HTTP_X_INVESTIGATOR_KVK_SOURCE"


def organisation_kvk(user: Any) -> str | None:
    """Return the KvK number of the organisation of the given user."""
    profile = getattr(user, "userprofile", None)
    organisation = getattr(profile, "organisation", None)
    kvk = getattr(organisation, "kvk_number", None)
    return kvk or None


def wants_organisation_kvk(request: Any, validated_data: dict[str, Any]) -> bool:
    """The organisation KvK is only used when explicitly requested."""
    if validated_data.get("use_organisation_kvk"):
        return True
    header = request.META.get(ORGANISATION_HEADER, "")
    return header.strip().lower() == "organisation"


def resolve_investigator_kvk(
    *,
    user: Any,
    explicit_kvk: str | None,
    use_organisation_kvk: bool,
    delivery_accountable_party: str | None,
    fallback_label: str = "deliveryAccountableParty",
) -> tuple[str, str]:
    """Return (kvk_number, log_line) describing which source was used.

    # CHECK: the principalInvestigator is not publicly available in the BRO
    # response, so we fall back to the deliveryAccountableParty. Confirm with the
    # data owner that this is acceptable for their corrections.
    """
    if explicit_kvk:
        return explicit_kvk, f"investigatorKvk uit de request gebruikt: {explicit_kvk}."

    if use_organisation_kvk:
        kvk = organisation_kvk(user)
        if not kvk:
            raise CorrectionValidationError(
                "use_organisation_kvk is opgegeven, maar de organisatie van deze "
                "gebruiker heeft geen kvk_number."
            )
        return kvk, f"investigatorKvk van de organisatie van de gebruiker: {kvk}."

    if delivery_accountable_party:
        return (
            delivery_accountable_party,
            f"investigatorKvk afgeleid van de {fallback_label} uit de BRO: "
            f"{delivery_accountable_party}.",
        )

    raise CorrectionValidationError(
        "Geen investigatorKvk bekend. Geef 'investigator_kvk' mee of zet "
        "'use_organisation_kvk' op true."
    )
