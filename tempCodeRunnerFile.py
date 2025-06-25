def add_select_unidad_param(url, hospital_name):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params['select_unidad'] = [hospital_to_unidad[hospital_name]['url_id']]

    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse(parsed_url._replace(query=new_query))

    return new_url