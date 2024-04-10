# Imports here


def construct_query_string(bound_word = " and ",
                           **params
                           ) -> str:
    """Construct a query string in the right format for the pandas 'query'
    function. The different params are bounded together in the query string with the
    bound word given by default. If one of the params is 'None', it is not
    included in the final query string."""

    # Instanciate query string
    query_string = ""

    # Iterate over the params to construct the query string
    for param_key, param in params.items():
        # Construct the param sub string if the param is not 'None'
        if param:
            query_sub_string = f"{param_key} == '{param}'"

            # Add to the query string
            query_string += f"{query_sub_string}{bound_word}"

    # Strip any remaining " and " at the end of the query string
    return query_string.strip(bound_word)
