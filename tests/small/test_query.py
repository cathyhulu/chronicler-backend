from chronicler_backend.schema import schema


def test_query():
    query = """
            query {
            books {
                title
            }

            authors {
                name
            }
            }
    """

    result = schema.execute_sync(
        query,
        variable_values={"title": "The Great Gatsby"},
    )

    assert result.errors is None
    assert result.data == {
        "books": [{"title": "Jurassic Park"}],
        "authors": [{"name": "Michael Crichton"}],
    }
