Managing products
=================

A product is anything you stock and count. Each one has a name, a SKU, a price and a
stock level.

Adding a product
----------------

1. Open **Products** from the sidebar.
2. Select **Add product**.
3. Fill in the name and SKU. Both are required.
4. Save.

.. warning::

   SKUs are unique. Saving a product with a SKU that already exists fails, and the
   form tells you which product already uses it.

Fields
------

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - What it holds
   * - Name
     - Yes
     - The name shown in lists and on invoices.
   * - SKU
     - Yes
     - Your stock-keeping code. Letters, digits and hyphens only.
   * - Price
     - No
     - Unit price in the account currency.
   * - Reorder point
     - No
     - Stock level at which the product is flagged for reordering. Leave empty to
       never flag it.

Setting a reorder point
-----------------------

Set the reorder point to the lowest stock level you are comfortable holding. The
dashboard flags any product at or below it.

Choosing a value
~~~~~~~~~~~~~~~~

A good starting point is one week of average sales plus the supplier's lead time.

Changing it later
~~~~~~~~~~~~~~~~~

Changes take effect immediately. Nothing is recalculated retroactively.

Archiving a product
-------------------

Archived products leave the product list but keep their history.

.. danger::

   Deleting a product removes its stock history for good. Archive instead unless you
   are certain.
