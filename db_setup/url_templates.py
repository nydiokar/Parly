# url_templates.py

BASE_URL = "https://www.ourcommons.ca/Members/en/"

URL_TEMPLATES = {
    "member_profile": BASE_URL + "{member_name}-{member_id}/xml",
    "member_roles": BASE_URL + "{member_name}-{member_id}/roles/xml",
    "member_votes": BASE_URL + "{member_name}-{member_id}/votes/xml",
    "bills_sponsored": "https://www.parl.ca/legisinfo/en/bills/xml?parlsession=all&sponsor={member_id}&advancedview=true",
    "recent_bills": "https://www.parl.ca/legisinfo/en/overview/json/recentlyintroduced",
    "bill_progress": "https://www.parl.ca/LegisInfo/en/bill/{parliament}-{session}/{bill_type}-{bill_number}/json?view=progress",
    "all_bills": "https://www.parl.ca/legisinfo/en/bill/{parliament}-{session}/{bill_type}-{bill_number}/json",
    "committee_interventions": "https://www.ourcommons.ca/publicationsearch/en/?per={member_id}&pubType=40017&xml=1",
    "chamber_interventions": "https://www.ourcommons.ca/publicationsearch/en/?per={member_id}&pubType=37&xml=1",
    "journal": "https://www.ourcommons.ca/publicationsearch/en/?View=D&Item=&ParlSes=44&oob=&Topic=&Proc=&Text=&RPP=15&order=&targetLang=&SBS=0&MRR=2000000&PubType=203&xml=1",
    "internal_economy_board": "https://www.ourcommons.ca/publicationsearch/en/?View=D&RPP=15&order=&SBS=0&MRR=2000000&PubType=10003&xml=1",
}

# Usage Example
# profile_url = URL_TEMPLATES['member_profile'].format(member_name="ziad-aboultaif", member_id=89156)
