# Writing tests

When thinking about writing tests for your code, and what *type* of tests to write, it's worth thinking about a 'testing pyramid'. [This is a great article on how to apply the pyramid practically](https://martinfowler.com/articles/practical-test-pyramid.html). The TLDR is:

1. Write tests with different granularity
2. The more high-level you get the fewer tests you should have

The current stack has integration/unit tests that use a [**django project testing strategy**](https://docs.djangoproject.com/en/4.1/topics/testing/overview/) for most. The tests are spead up mainly by running them in parallel, by default, but can be optimised to reuse the existing database. All the tests run relatively quickly, one test is slow to run, especially when working with the generated Postgres database, but very fast if isolated and mocked

The basic set to look at for TDD:
1. [Unit/integration tests](#Unit/integration-tests)

### Unit/integration tests

**frameworks:** Pytest, Python

**what:** For low-cost granular testing of specific functions/utilities as well as integration with Django. Capture edge cases or unhappy paths. Anything outside of the function under test should be mocked/faked/stubbed. 

**where:** As close to what's being under test as possible. e.g. in a __test__ folder at the same level. 

**examples:** Every test file must be prefixed with *test*, including the functions/class methods that test  scenarios

An example of tests with different mocks can be found [here](../datahub/core/test/test_serializers.py) 

An example of tests with mixin logic can be found [here](datahub/company/test/test_company_matching_api.py)

An example of an integration test with the database can be found [here](datahub/company/test/test_models.py)

**how to run:** [Running tests](./Running%20tests.md)