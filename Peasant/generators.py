
def genVoyagerSearchPath(company_id,start,max_facet_values=10):
    '''Generate a URL for the Voyarger API.

    company_id - str - Company identifier
    start - int - Integer value indicating the offset for record extraction
    max_facet_vales - int - Count of profiles to request
    '''

    mfv = max_facet_values
    cid = company_id
    return '/voyager/api/search/hits' \
            '?count=12&educationEndYear=List()&educationStartYear=List()' \
            f'&facetCurrentCompany=List({cid})' \
            '&facetCurrentFunction=List()&facetFieldOfStudy=List()' \
            '&facetGeoRegion=List()&facetNetwork=List()&facetSchool=List()' \
            f'&facetSkillExplicit=List()&keywords=List()&maxFacetValues={mfv}' \
            f'&origin=organization&q=people&start={start}' \
            '&supportedFacets=List(GEO_REGION,SCHOOL,CURRENT_COMPANY,' \
            'CURRENT_FUNCTION,FIELD_OF_STUDY,SKILL_EXPLICIT,NETWORK)'
