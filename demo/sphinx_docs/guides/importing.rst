Importing products
==================

You can create many products at once from a CSV file.

The file format
---------------

The first row must name the columns. Name and SKU are required, the rest optional.

.. code-block:: text

   name,sku,price,reorder_point
   Widget,WID-001,4.50,20
   Gadget,GAD-002,12.00,

Running an import from the command line
---------------------------------------

Administrators can import directly on the server:

.. code-block:: bash

   python manage.py import_products products.csv --dry-run

Through the API
---------------

.. code-block:: python

   import requests

   response = requests.post(
       "https://inventory.example.com/api/products/import/",
       files={"file": open("products.csv", "rb")},
       headers={"Authorization": f"Token {token}"},
   )
   response.raise_for_status()
   print(response.json()["created"], "products created")

The ``created`` key holds the number of new products. Rows that fail validation are
listed under ``errors`` with the row number and the reason.

When an import fails
--------------------

Nothing is saved unless every row is valid. Fix the rows listed and run it again.

.. seealso::

   :doc:`../reference/settings` for the maximum file size.
