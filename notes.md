# Notes

## Company ID

API requests require a company ID, which can be obtained from the
profile page of the company: `/company/<company_name>/people/`. See
the function `Peasant.parsers.parseCompanyId` for the regexp used
to extract this value.

## Headers required by API

API requiests require a `csrf-token` header, which is the same value
as the `JSESSIONID` cookie, and API version (`x-restli-protocol-version`),
which has been hardcoded at `2.0.0`.

## API Request Parameters

API request records are controlled using query parameters. See
`Peasant.generators.genVoyagerURL` for more information on these.

## JSON Paths for Information Extraction

- result_count: `/metadata/totalResultCount`
- elements (profiles): `/elements`
- path for basic profile information on an element:
    /hitInfo/com.linkedin.voyager.search.SearchProfile
- location/industry information: ^ ending with `location` or `industry`

See `Peasant.extractors` for more information on extracting values from
the JSON response.

## Execution Notes

1. Get the company identifier
2. Update request headers with proper values (CSRF token, API version)
3. Generate the initial API request
4. Extract profiles and total request count
5. Make requsts for all remaining profiles, extracting values along the way
