import json
from datetime import datetime
from pyegeria import CollectionManager, PyegeriaInvalidParameterException, PyegeriaConnectionException, \
    PyegeriaAPIException, PyegeriaUnknownException, print_basic_exception
from rich import print_json
from validators import ValidationError


def test_create_digital_product_catalog():
    try:
        c_client = CollectionManager("qs-view-server",
                                     "https://localhost:9443",
                                     user_id="erinoverview", )

        token = c_client.create_egeria_bearer_token("erinoverview",
                                                    "secret")
        # start_time = time.perf_counter()
        display_name = "Antenna Reference Products"
        description = "A catalog of data products about antennas"
        classification_name = None
        q_name = c_client.__create_qualified_name__("DigProdCatalog", display_name, version_identifier="")
        body = {
            "class": "NewElementRequestBody",
            "isOwnAnchor": True,
            "properties": {
                "class": "DigitalProductCatalogProperties",
                "qualifiedName": q_name,
                "displayName": display_name,
                "description": description,
                "category": "Amateur Radio"
            }
        }

        response = c_client.create_digital_product_catalog(body)
        # duration = time.perf_counter() - start_time
        # resp_str = json.loads(response)
        # print(f"\n\tDuration was {duration} seconds\n")
        if type(response) is dict:
            print_json(json.dumps(response, indent=4))
        elif type(response) is str:
            print("\n\nGUID is: " + response)
        assert True

    except (PyegeriaInvalidParameterException, PyegeriaConnectionException, PyegeriaAPIException,
            PyegeriaUnknownException,) as e:
        print_basic_exception(e)
        assert False, "Invalid request"
    except ValidationError as e:
        print(e)
    finally:
        c_client.close_session()