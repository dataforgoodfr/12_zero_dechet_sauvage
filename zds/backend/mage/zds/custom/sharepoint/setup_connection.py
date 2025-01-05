from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext

if "custom" not in globals():
    from mage_ai.data_preparation.decorators import custom
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@custom
def transform_custom(*args, **kwargs):
    """
    args: The output from any upstream parent blocks (if applicable)
    https://subash-mishra.medium.com/sharepoint-with-python-a-comprehensive-guide-to-working-sharepoint-online-file-and-folders-using-ce2778cdf8f3

    Returns:
        Anything (e.g. data frame, dictionary, array, int, str, etc.)
    """

    # SharePoint Credentials
    client_id = "ddd127c2-1138-4091-aa4d-91fc8412c875"
    client_secret = "1WC6a/4ANFY6109qLhSTiuHgVo0+Rl8YVYvVJxtGQiY="

    client_credentials = ClientCredential(client_id, client_secret)
    ctx = ClientContext("{url}").with_credentials(
        client_credentials,
        environment="GCCH",
    )
    ctx.web.get().execute_query()

    # ------------------------------------------------------------------------------------
    # # SharePoint site URL based on the company's domain name and team
    # # Authentication context using client_id and client_secret
    # if context_auth.acquire_token_for_app(
    # ):
    #     # Create SharePoint client context
    # # Download file content
    #     .download(out)
    #     .execute_query()
    # ------------------------------------------------------------------------------------

    #     if context_auth.acquire_token_for_app(
    #     ):
    #         # Create SharePoint client context
    #     # Print error message if an exception occurs during SharePoint context establishment


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, "The output is undefined"
