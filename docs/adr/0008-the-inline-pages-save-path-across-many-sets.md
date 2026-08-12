# ADR 0008 — The inline page's save path, across any number of sets

**Status:** accepted

**Supersedes:** [ADR 0005](0005-the-inline-view-save-path.md). That decision was right and is kept
whole. It is restated here because the class and the attribute it named no longer exist, and
because two of its steps need more saying once a page can carry several sets.

## Decision

On submission the page does this, in this order:

1. Validate **every** set, even after one has already failed, using Django's `all_valid`. It is
   also validated on the path where the parent form itself is invalid.
2. Inside one `transaction.atomic()` block: save the parent, then attach it to each set and save
   the sets.
3. **After** the block: resolve the success URL.
4. Queue the success message and return the redirect directly.

`super().form_valid()` is never called.

Where a set declares `max_num`, its factory also gets `validate_max=True`; where it declares
`min_num`, it gets `validate_min=True`. `absolute_max` is left at Django's default and is never
derived from the cap. Each set's limits are enforced against that set's own submitted rows and
never against a page-wide total.

## Why

**Everything is validated because a page that stops at the first failure hides errors that exist.**
Django's `all_valid` uses a list comprehension rather than a generator specifically to defeat
`all()`'s short-circuit, so every set accumulates its errors for the redisplay. The check also has
to run on the invalid-parent path, which Django routes straight to `form_invalid` without touching
the sets. That one is easy to get wrong and easy to believe you have got right: `formset.errors`
and `formset.non_form_errors` both validate on access, so a test that reads either passes whether
or not the view validated anything.

**One transaction, because the page is one submission.** A parent saved with its second set
rejected leaves a record nobody intended to create. The parent is saved first because the rows need
its primary key, and they pick it up by object identity — the unsaved instance handed to each set at
construction is the same object the save assigns a key to.

**The success URL is resolved after the block, not before.** Resolving it earlier breaks creation,
where the object has no key yet: a view with no explicit success URL raises after the rows have
already committed, and one pointing at the detail page redirects to an unresolved path. Resolving
afterwards also means `get_absolute_url()` reflects what was stored rather than what was pending.

**`super().form_valid()` is not called** because it reaches Django's `ModelFormMixin.form_valid`,
which saves the parent a second time, outside the transaction.

**The cap is validated but the absolute ceiling is not derived from it.** `inlineformset_factory`
defaults `validate_max` to `False`, so a cap on its own rejects nothing. Bounding `absolute_max` to
the cap looks like defence in depth and is not: Django reads the raw submitted form count before
subtracting rows marked for deletion, and discards everything past the bound before validation
runs. A submission legitimately within its cap after removals would be silently truncated.

## Consequences

Sets are saved in the order the view lists them. Nothing depends on that order, and the display
order hook deliberately does not touch it.

The formsets are built once per request and reused. The page renders the same objects that were
validated, and a page carrying several sets does not repeat their queries or their configuration
checks.
