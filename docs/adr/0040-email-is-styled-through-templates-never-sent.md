# ADR 0040 — Email is styled through templates, never sent

**Status:** accepted

## Decision

django-mvp gives email its look and never renders or sends it. It ships a base email template, `mvp/email/base.html`, that an email's HTML template extends, the email pieces (`c-mvp.email.text`, `.button`, `.note`, `.divider`, `.code`) and the `mvp_email` template tags. The base template inlines its own styles as it renders, through `{% email_inline %}`, so whatever renders and sends the email gets HTML that mail clients can show. The subject, the plain-text part, the language, the recipients and the delivery stay with the sender.

A package built on django-mvp brands the email of a third-party package it wraps by overriding that package's HTML email templates to extend the base template. It never asks the wrapped package to send email another way.

## Why

Sending is usually built into the package being wrapped, and a package built on django-mvp cannot change it. django-mvp-accounts cannot change how allauth sends mail, only override the templates allauth renders. A helper class for sending would have worked only for code that called it, which excludes the packages whose email most needs the brand. Inlining while the template renders, rather than at send time, is what lets the look survive any sender.

This follows the package's aim of a consistent face around the packages projects rely on, without extending or replacing them.

## Revisit if

A wrapped package exposes a hook for transforming its outgoing messages that every sender honours, or django-mvp starts sending email of its own.
