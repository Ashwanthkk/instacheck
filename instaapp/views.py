import json
import re
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from django.http import FileResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from instacheck.asset.backend.Module import insta

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_ROOT = BASE_DIR / 'instacheck'


def home(request):
    return render(request, 'index.html')


def serve_html(request, filename):
    requested = (FRONTEND_ROOT / filename).resolve()
    if FRONTEND_ROOT not in requested.parents and requested != FRONTEND_ROOT:
        return HttpResponseBadRequest('Invalid frontend path.')

    if not requested.exists() or not requested.is_file():
        return HttpResponseBadRequest('Frontend file not found.')

    return FileResponse(open(requested, 'rb'), content_type='text/html')


def _matches_followers_file(name: str) -> bool:
    normalized = name.replace('\\', '/').lower()
    return bool(re.search(r'(^|/)followers(?:[_-]?\d*)?\.json$', normalized))


def _matches_following_file(name: str) -> bool:
    normalized = name.replace('\\', '/').lower()
    return bool(re.search(r'(^|/)following(?:[_-]?\d*)?\.json$', normalized))


def _matches_html_file(name: str) -> bool:
    normalized = name.replace('\\', '/').lower()
    return bool(re.search(r'(^|/)(followers(?:[_-]?\d*)?|following(?:[_-]?\d*)?)\.html$', normalized))


def _is_json_request(request):
    accept = request.headers.get('Accept', '')
    requested_with = request.headers.get('X-Requested-With', '')
    return (
        'application/json' in accept
        or requested_with == 'XMLHttpRequest'
        or request.content_type == 'application/json'
    )


@csrf_exempt
def upload_zip(request):
    if request.method != 'POST':
        if _is_json_request(request):
            return JsonResponse({'error': 'Only POST is allowed.'}, status=405)
        return render(request, 'index.html', {'error': 'Only POST is allowed.'}, status=405)

    zip_file = request.FILES.get('zip_file')
    if zip_file is None:
        err = 'Missing zip_file upload.'
        if _is_json_request(request):
            return JsonResponse({'error': err}, status=400)
        return render(request, 'index.html', {'error': err}, status=400)

    try:
        archive = ZipFile(zip_file)
    except BadZipFile:
        err = 'Uploaded file is not a valid ZIP archive.'
        if _is_json_request(request):
            return JsonResponse({'error': err}, status=400)
        return render(request, 'index.html', {'error': err}, status=400)

    entries = [name for name in archive.namelist() if not name.endswith('/')]
    html_entries = sorted(name for name in entries if _matches_html_file(name))
    follower_entries = sorted(name for name in entries if _matches_followers_file(name))
    following_entries = sorted(name for name in entries if _matches_following_file(name))

    if html_entries:
        err = 'HTML files are not supported. Please upload JSON files from the Instagram export ZIP.'
        if _is_json_request(request):
            return JsonResponse({'error': err}, status=400)
        return render(request, 'index.html', {'error': err}, status=400)

    if not follower_entries or not following_entries:
        err = 'Could not find followers or following JSON files in the uploaded ZIP.'
        if _is_json_request(request):
            return JsonResponse({'error': err}, status=400)
        return render(request, 'index.html', {'error': err}, status=400)

    followers_data = []
    for name in follower_entries:
        try:
            payload = json.loads(archive.read(name).decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            err = 'One of the follower JSON files is invalid.'
            if _is_json_request(request):
                return JsonResponse({'error': err}, status=400)
            return render(request, 'index.html', {'error': err}, status=400)

        if isinstance(payload, list):
            followers_data.extend(payload)
        elif isinstance(payload, dict):
            followers_data.append(payload)
        else:
            err = 'Follower JSON data is in an unsupported format.'
            if _is_json_request(request):
                return JsonResponse({'error': err}, status=400)
            return render(request, 'index.html', {'error': err}, status=400)

    following_data = {}
    for name in following_entries:
        try:
            payload = json.loads(archive.read(name).decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            err = 'One of the following JSON files is invalid.'
            if _is_json_request(request):
                return JsonResponse({'error': err}, status=400)
            return render(request, 'index.html', {'error': err}, status=400)

        if isinstance(payload, dict):
            following_data = payload
            break

    if not following_data:
        err = 'The following JSON payload is empty or invalid.'
        if _is_json_request(request):
            return JsonResponse({'error': err}, status=400)
        return render(request, 'index.html', {'error': err}, status=400)

    checker = insta(followers_data, following_data)
    non_followers, total_followers, total_following, non_follower_count = checker.non_followers()
    followers = checker.extract_follower_usernames()
    following = checker.extract_following_usernames()

    if _is_json_request(request):
        return JsonResponse({
            'followers': followers,
            'following': following,
            'non_followers': non_followers,
            'total_followers': total_followers,
            'total_following': total_following,
            'non_follower_count': non_follower_count,
        })

    non_followers_list = []
    for link in non_followers:
        clean_link = str(link)
        parts = [p for p in clean_link.rstrip('/').split('/') if p]
        username = parts[-1] if parts else clean_link
        non_followers_list.append({
            'username': username,
            'url': clean_link,
        })

    return render(request, 'results.html', {
        'followers': followers,
        'following': following,
        'non_followers': non_followers,
        'non_followers_list': non_followers_list,
        'total_followers': total_followers,
        'total_following': total_following,
        'non_follower_count': non_follower_count,
        'has_results': True,
    })
