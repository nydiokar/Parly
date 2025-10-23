# url_templates.py

BASE_URL = "https://www.ourcommons.ca/Members/en/"

URL_TEMPLATES = {
    "member_profile": BASE_URL + "{search_pattern}/",
    "member_roles": BASE_URL + "{search_pattern}/roles",
    "member_votes": BASE_URL + "{search_pattern}/votes/xml",
    "bills_sponsored": "https://www.parl.ca/legisinfo/en/bills/xml?parlsession=all&sponsor={member_id}&advancedview=true",
    "recent_bills": "https://www.parl.ca/legisinfo/en/overview/json/recentlyintroduced",
    "bill_progress": "https://www.parl.ca/LegisInfo/en/bill/{parliament}-{session}/{bill_type}-{bill_number}/json?view=progress",
    "all_bills": "https://www.parl.ca/legisinfo/en/bill/{parliament}-{session}/{bill_type}-{bill_number}/json",

    # Bill Full Text XML (has summary + full legislative text!)
    # Pattern: /Bills/{parl}{sess}/{chamber}/{billtype}-{num}/{billtype}-{num}_1/{billtype}-{num}_E.xml
    # chamber: "Government" or "Private"
    # _1 seems to be version (always 1 for initial?)
    # _E = English, _F = French
    "bill_text_xml": "https://www.parl.ca/Content/Bills/{parliament}{session}/{chamber}/{bill_type}-{bill_number}/{bill_type}-{bill_number}_1/{bill_type}-{bill_number}_E.xml",
    "committee_interventions": "https://www.ourcommons.ca/publicationsearch/en/?per={member_id}&pubType=40017&xml=1",
    "chamber_interventions": "https://www.ourcommons.ca/publicationsearch/en/?per={member_id}&pubType=37&xml=1",
    "journal": "https://www.ourcommons.ca/publicationsearch/en/?View=D&Item=&ParlSes=44&oob=&Topic=&Proc=&Text=&RPP=15&order=&targetLang=&SBS=0&MRR=2000000&PubType=203&xml=1",
    "internal_economy_board": "https://www.ourcommons.ca/publicationsearch/en/?View=D&RPP=15&order=&SBS=0&MRR=2000000&PubType=10003&xml=1",

    # Journal PDFs (Sitting records with motion text)
    "journal_pdf": "https://www.ourcommons.ca/Content/House/{parliament}{session}/Journals/{sitting:03d}/Journal{sitting:03d}.PDF",
    "journal_viewer": "https://www.ourcommons.ca/documentviewer/en/{parliament}-{session}/house/sitting-{sitting}/journals",

    # Votes
    "vote_detail": "https://www.ourcommons.ca/members/en/votes/{parliament}/{session}/{vote_number}",
    "vote_detail_party": "https://www.ourcommons.ca/members/en/votes/{parliament}/{session}/{vote_number}?view=party",

    # Petitions
    "petitions_xml": "https://www.ourcommons.ca/petitions/en/Petition/Search",
    # Params: parl=X (optional), Category=All, order=Recent, output=xml
    "petition_detail": "https://www.ourcommons.ca/petitions/en/Petition/Details?Petition={petition_id}",
}

# Usage Examples:
# profile_url = URL_TEMPLATES['member_profile'].format(search_pattern="ziad-aboultaif(89156)")
# journal_pdf = URL_TEMPLATES['journal_pdf'].format(parliament=45, session=1, sitting=26)
#   Result: https://www.ourcommons.ca/Content/House/451/Journals/026/Journal026.PDF
# vote_url = URL_TEMPLATES['vote_detail'].format(parliament=45, session=1, vote_number=39)
# petitions = URL_TEMPLATES['petitions_xml'] + "?parl=44&Category=All&order=Recent&output=xml"
