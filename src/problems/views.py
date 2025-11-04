# from django.shortcuts import render

# # Create your views here.
# # problems/views.py
# import json, logging
# from django.http import JsonResponse, HttpResponseNotAllowed
# from django.views.decorators.csrf import csrf_exempt

# logger = logging.getLogger("health")

# @csrf_exempt
# def health_check(request):
#     try:
#         if request.method == "GET":
#             return JsonResponse({"status": "ok", "method": "GET"})
#         if request.method == "POST":
#             try:
#                 body = json.loads(request.body or b"{}")
#             except json.JSONDecodeError:
#                 return JsonResponse({"detail": "Invalid JSON"}, status=400)
#             return JsonResponse({"status": "ok", "method": "POST", "echo": body})
#         return HttpResponseNotAllowed(["GET", "POST"])
#     except Exception:
#         logger.exception("health_check error")
#         return JsonResponse({"detail": "Internal Server Error"}, status=500)

import re
import datetime as dt
import json, logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .mongo import problems_col
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger("health")

DIFFICULTIES = {"Easy", "Medium", "Hard"}

@csrf_exempt
def health_check(request):
    """
    GET  /api/healthz  -> {"status":"ok","method":"GET"}
    POST /api/healthz  -> echoes JSON body: {"status":"ok","method":"POST","echo":{...}}
    Other methods      -> 405
    """
    try:
        if request.method == "GET":
            return JsonResponse({"status": "ok", "method": "GET"})
        if request.method == "POST":
            try:
                body = json.loads(request.body or b"{}")
            except json.JSONDecodeError:
                return JsonResponse({"detail": "Invalid JSON"}, status=400)
            return JsonResponse({"status": "ok", "method": "POST", "echo": body})
        return HttpResponseNotAllowed(["GET", "POST"])
    except Exception:
        logger.exception("health_check error")
        return JsonResponse({"detail": "Internal Server Error"}, status=500)


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

def normalize_problem(p: dict) -> dict:
    """
    Minimal LeetCode-like problem document.
    Required: title, difficulty, categories (list[str])
    Optional: source (default 'LeetCode'), url
    """
    title = (p.get("title") or "").strip()
    difficulty = (p.get("difficulty") or "").strip()
    categories = p.get("categories", [])

    if not title:
        raise ValueError("title is required")
    if difficulty not in DIFFICULTIES:
        raise ValueError("difficulty must be one of Easy/Medium/Hard")
    if not isinstance(categories, list) or not categories:
        raise ValueError("categories must be a non-empty list of strings")

    categories = [str(c).strip() for c in categories if str(c).strip()]
    now = dt.datetime.utcnow()

    doc = {
        "slug": slugify(title),
        "title": title,
        "difficulty": difficulty,
        "categories": categories,
        "category_slugs": [slugify(c) for c in categories],
        "updated_at": now,
    }
    doc["_created_at"] = now  # used only on first insert
    return doc

class ProblemsView(APIView):
    """
    POST /api/problems
      - Body: a single problem object OR a JSON list of problem objects.
      - Upserts by slug (safe to re-run).

    GET /api/problems
      - Lists all problems (sorted by title).
    """

    def post(self, request):
        payload = request.data
        items = payload if isinstance(payload, list) else [payload]

        normalized = []
        # Validate & normalize
        try:
            for item in items:
                normalized.append(normalize_problem(item))
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Upsert each by slug
        upserted = 0
        results = []
        for doc in normalized:
            slug = doc["slug"]
            update = {
                "$set": {
                    "title": doc["title"],
                    "difficulty": doc["difficulty"],
                    "categories": doc["categories"],
                    "category_slugs": doc["category_slugs"],
                    "updated_at": doc["updated_at"],
                },
                "$setOnInsert": {
                    "slug": slug,
                    "created_at": doc["_created_at"],
                },
            }
            res = problems_col.update_one({"slug": slug}, update, upsert=True)
            if res.upserted_id is not None or res.modified_count > 0:
                upserted += 1
            results.append({"slug": slug, "status": "ok"})

        return Response({"upserted": upserted, "results": results}, status=status.HTTP_201_CREATED)

    def get(self, request):
        print("hello")
        cursor = problems_col.find({}, {"_id": 0}).sort([("title", 1)])
        return Response(list(cursor), status=status.HTTP_200_OK)

