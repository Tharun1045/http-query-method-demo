# The HTTP QUERY Method Is Here — And It's Worth Knowing About

If you've ever built a search API, you've probably faced this exact dilemma.

You need to filter products by category, price range, rating, stock status, and maybe a few more fields. You reach for `GET`... but the URL starts looking like a phone number. You switch to `POST /search`... and it works, but something feels semantically off.

That discomfort has a name — and now it has a solution.

---

## The Problem with GET for Complex Search

`GET` is the natural choice for read-only data. But the URL has limits.

Browsers and proxies often cap URLs at around 2KB. Add 15 filter fields, some with nested values, and you blow past that quickly. Add sensitive values like customer IDs or location data, and now those filters are sitting in your server access logs in plain text.

So what do most developers do?

---

## The Workaround: POST /search

Teams reach for `POST`. Send the filters in a clean JSON body. No URL limit. No encoding mess. Sensitive data stays out of logs.

It works great in practice. I've used it. You've probably used it. Most large APIs use it.

But here's the semantic problem: `POST` is defined by the HTTP specification as **unsafe** and **non-idempotent**. It's designed for operations that *change* something — creating a record, submitting a payment, sending a message.

When we use `POST` for a read-only search, we're telling CDNs, proxies, and HTTP clients that this request might modify data. So they won't cache it. They won't automatically retry it on a network drop. And some strict WAF configurations will treat it differently from a GET.

We're solving a real problem, but bending the rules to do it.

---

## The Clean Solution: HTTP QUERY (RFC 10008)

RFC 10008 formalises the HTTP `QUERY` method — designed exactly for this pattern.

```http
QUERY /products
Content-Type: application/json

{
  "category": "kitchen",
  "max_price": 50.0,
  "min_rating": 4.5,
  "in_stock": true
}
```

QUERY gives you:
- **A request body** — no URL length limit
- **Safe** — explicitly read-only in the spec
- **Idempotent** — clients can retry safely
- **Cacheable** — intermediaries can cache on URL + body hash

It's GET with a body. That's what we always needed.

---

## Does QUERY Make Your API Faster?

No. And this is important to understand.

The HTTP method is a semantic label. It tells clients and infrastructure *what kind of operation* this is. It doesn't change how your database runs the query or how your server processes the filters.

In my demo project, I added a `processing_time_ms` field to every response. GET, POST, and QUERY return virtually identical timings for the same filters.

> QUERY solves an **API design problem**, not a **database performance problem**.

---

## Should You Use It in Production Today?

Honestly — proceed carefully.

- Old reverse proxies and WAF rules may block unknown HTTP methods
- Most CDNs don't yet cache QUERY responses by default
- Not all client libraries have a built-in `query()` method
- Browser CORS will require an OPTIONS preflight for QUERY

For **internal microservices** or **modern API gateways** that you control — QUERY is excellent and I'd encourage experimenting with it.

For **public-facing APIs** — `POST /search` remains the safe, pragmatic choice until tooling catches up.

---

## 🛠 Try It Yourself

I built a simple demo in Python (zero dependencies, just the standard library) that implements all three patterns side-by-side — GET, POST /search, and QUERY — with identical filter logic so you can compare the responses directly.

👉 GitHub: https://github.com/Tharun1045/http-query-method-demo

Clone it, run `python app.py`, and test with the curl examples in the README. Each response includes `safe`, `idempotent`, and `processing_time_ms` so the differences are immediately visible.

---

Have you used QUERY in a real project yet? Still on `POST /search`? I'd love to hear where the industry is landing on this.

#webdevelopment #api #backend #http #python #softwareengineering #restapi
