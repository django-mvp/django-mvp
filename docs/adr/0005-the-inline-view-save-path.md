# ADR 0005 — The inline view's save path

**Status:** accepted

## Decision

`InlineFormsetMixin.form_valid` does four things in this order:

1. Validate the formset; delegate to `form_invalid` if it fails.
2. Inside one `transaction.atomic()` block: save the parent, assign it to `formset.instance`, save
   the formset.
3. **After** the block: resolve the success URL.
4. Queue the success message and return the redirect directly.

`super().form_valid()` is never called. Where `inline_max_num` is set,
`get_formset_factory_kwargs()` also sets `validate_max=True`, and leaves `absolute_max` at Django's
default.

## Why

Each step is there because the obvious alternative is wrong in a way that is invisible until it
bites.

**The transaction** is a requirement on the feature rather than an assumption about the database.
Django wraps a view in a transaction only when the consuming project sets `ATOMIC_REQUESTS`, which
a published package cannot rely on. A view that saves the parent and then fails on a row leaves a
record the user never intended.

**`super().form_valid()` is skipped** because it reaches `SuccessMessageMixin`, which delegates to
`ModelFormMixin.form_valid`, whose first statement is `self.object = form.save()`. Calling it after
the block would save the parent a second time, outside the transaction and after the rows were
written — an extra `UPDATE`, a second `_save_m2m`, and a consuming project's `post_save` receivers
firing twice for one user action.

**The success URL is resolved after the saves** because on the create path `self.object` is `None`
until then. The packaged success-URL chain falls back to `object.get_absolute_url()`, which raises
`ImproperlyConfigured` with no object, and a CRUD shorthand like `"detail"` cannot resolve without
a primary key, so it is returned as a literal relative path. Both failures happen after the rows
have committed. `MVPDeleteView` resolves its URL first, but only because its object is about to be
deleted; that reason does not transfer.

**The message is queued outside the block** because Django's message storage is not transactional.
A flash queued inside would survive a rollback, telling the user a record was saved when nothing
was.

**`absolute_max` is not derived from the cap.** Django's `absolute_max` check reads the raw
submitted `TOTAL_FORMS` and, unlike the `validate_max` check beside it, does not subtract the rows
marked for deletion. A user working within a cap of three who adds four rows and removes two
submits five forms with two `DELETE` flags: `validate_max` passes, and a cap-derived `absolute_max`
would reject it anyway. Worse, `total_form_count()` clamps to `absolute_max`, so rows past the
bound are never constructed and never re-rendered, and what the user typed is lost. Worst, a record
whose rows already exceed the cap could never be brought back into compliance, because the
submission removing the surplus is exactly the one refused.

## Revisit if

Django changes `ModelFormMixin.form_valid` to stop saving, or the package adopts `ATOMIC_REQUESTS`
as a documented requirement of consuming projects.
