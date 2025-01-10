import strawberry


def test_query(schema_fixture: strawberry.Schema):
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

    result = schema_fixture.execute_sync(
        query,
        variable_values={"title": "The Great Gatsby"},
    )

    assert result.errors is None
    assert result.data == {
        "books": [{"title": "Jurassic Park"}],
        "authors": [{"name": "Michael Crichton"}],
    }
