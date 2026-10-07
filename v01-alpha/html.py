"""LocalAcademy - All HTML Templates"""
from jinja2 import DictLoader

def setup_templates(app):
	app.jinja_loader = DictLoader(TEMPLATES)

TEMPLATES = {

'base.html': """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{% block title %}LocalAcademy{% endblock %}</title>
<script src="https://cdn.tailwindcss.com"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/epubjs/dist/epub.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root {
--color-primary: {{ theme_colors.primary if theme_colors is defined else '#3b82f6' }};
--color-secondary: {{ theme_colors.secondary if theme_colors is defined else '#8b5cf6' }};
--color-accent: {{ theme_colors.accent if theme_colors is defined else '#06b6d4' }};
--color-bg: {{ theme_colors.bg if theme_colors is defined else '#0f1419' }};
}
[x-cloak]{display:none!important}body{background:var(--color-bg);color:#e4e6eb}
.sidebar{background:#1a1f2e;border-right:1px solid #2d3748;transition:transform .2s}
.nav-item{transition:all .2s}.nav-item:hover{background:#2d3748;border-left:3px solid #3b82f6}
.nav-item.active{background:#2d3748;border-left:3px solid var(--color-primary)}
.card{background:#1a1f2e;border:1px solid #2d3748;border-radius:.5rem;transition:all .3s}
.card:hover{border-color:var(--color-primary);transform:translateY(-2px);box-shadow:0 4px 12px rgba(59,130,246,.1)}
.btn-primary{background:var(--color-primary);color:#fff;padding:.5rem 1rem;border-radius:.375rem;transition:all .2s}
.btn-primary:hover{background:var(--color-secondary)}
.btn-secondary{background:#374151;color:#fff;padding:.5rem 1rem;border-radius:.375rem;transition:all .2s}
.btn-secondary:hover{background:#4b5563}
.input-field{background:#0f1419;border:1px solid #2d3748;color:#e4e6eb;padding:.5rem 1rem;border-radius:.375rem;width:100%}
.input-field:focus{outline:none;border-color:var(--color-primary)}
.badge{padding:.25rem .75rem;border-radius:9999px;font-size:.75rem;font-weight:600}
.badge-success{background:#10b981;color:#fff}.badge-warning{background:#f59e0b;color:#fff}
::-webkit-scrollbar{width:8px}::-webkit-scrollbar-track{background:#1a1f2e}
::-webkit-scrollbar-thumb{background:var(--color-primary);border-radius:4px}
input[type="checkbox"]{appearance:none;width:18px;height:18px;border:2px solid var(--color-primary);border-radius:4px;background:#0f1419;cursor:pointer;position:relative}
input[type="checkbox"]:checked{background:var(--color-primary)}
input[type="checkbox"]:checked::after{content:'\\2713';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#fff;font-size:12px}
input[type="range"]{appearance:none;background:transparent;cursor:pointer}
input[type="range"]::-webkit-slider-track{height:4px;background:#374151;border-radius:2px}
input[type="range"]::-webkit-slider-thumb{appearance:none;width:14px;height:14px;background:var(--color-primary);border-radius:50%;margin-top:-5px}
canvas{max-width:100%;height:auto}
</style>
{% block extra_head %}{% endblock %}
</head>
<body x-data="{menu:false}" class="antialiased">
<div class="flex h-screen overflow-hidden">
<aside x-show="menu" x-transition:enter="transition ease-out duration-200" x-transition:leave="transition ease-in duration-150" class="sidebar w-64 flex-shrink-0 overflow-y-auto">
<div class="p-6"><h1 class="text-2xl font-bold text-blue-400"><i class="fas fa-graduation-cap mr-2"></i>LocalAcademy</h1></div>
<nav class="px-4 space-y-2">
<a href="{{ url_for('main.index') }}" class="nav-item flex items-center px-4 py-3 rounded-lg {{ 'active' if request.endpoint=='main.index' else '' }}"><i class="fas fa-home mr-3"></i>Dashboard</a>
<a href="{{ url_for('courses.index') }}" class="nav-item flex items-center px-4 py-3 rounded-lg {{ 'active' if 'courses' in (request.endpoint or '') else '' }}"><i class="fas fa-book mr-3"></i>Courses</a>
<a href="{{ url_for('creators.index') }}" class="nav-item flex items-center px-4 py-3 rounded-lg {{ 'active' if 'creators' in (request.endpoint or '') else '' }}"><i class="fas fa-user mr-3"></i>Creators</a>
<a href="{{ url_for('categories.index') }}" class="nav-item flex items-center px-4 py-3 rounded-lg {{ 'active' if 'categories' in (request.endpoint or '') else '' }}"><i class="fas fa-folder mr-3"></i>Categories</a>
<a href="{{ url_for('tags.index') }}" class="nav-item flex items-center px-4 py-3 rounded-lg {{ 'active' if 'tags' in (request.endpoint or '') else '' }}"><i class="fas fa-tag mr-3"></i>Tags</a>
<a href="{{ url_for('settings.index') }}" class="nav-item flex items-center px-4 py-3 rounded-lg {{ 'active' if 'settings' in (request.endpoint or '') else '' }}"><i class="fas fa-cog mr-3"></i>Settings</a>
</nav>
</aside>
<main class="flex-1 overflow-y-auto">
<header class="bg-gray-900 border-b border-gray-700 px-6 py-4">
<div class="flex items-center justify-between">
<div class="flex items-center space-x-4">
<button @click="menu=!menu" class="text-gray-400 hover:text-white px-2 py-1 rounded hover:bg-gray-700"><i class="fas fa-bars text-lg"></i></button>
<h2 class="text-xl font-semibold">{% block page_title %}Dashboard{% endblock %}</h2>
</div>
<div x-data="{q:'',res:[],open:false}" class="relative">
<input type="text" x-model="q" @input.debounce="fetch('/search?q='+q).then(r=>r.json()).then(d=>{res=d;open=true})" @click.away="open=false" placeholder="Search..." class="input-field w-64">
<div x-show="open&&(res.courses?.length>0||res.files?.length>0)" x-cloak class="absolute right-0 mt-2 w-96 bg-gray-800 rounded-lg shadow-xl border border-gray-700 z-50 max-h-96 overflow-y-auto">
<div x-show="res.courses?.length>0" class="p-4 border-b border-gray-700"><h3 class="text-sm font-semibold text-gray-400 mb-2">Courses</h3>
<template x-for="c in res.courses||[]" :key="c.id"><a :href="'/courses/'+c.id" class="block p-2 hover:bg-gray-700 rounded" x-text="c.display_name"></a></template></div>
<div x-show="res.files?.length>0" class="p-4"><h3 class="text-sm font-semibold text-gray-400 mb-2">Files</h3>
<template x-for="f in res.files||[]" :key="f.id"><a :href="'/player/'+f.file_hash" class="block p-2 hover:bg-gray-700 rounded text-sm" x-text="f.file_name"></a></template>
</div></div>
</div>
</div>
</header>
{% with messages=get_flashed_messages(with_categories=true) %}{% if messages %}
<div class="px-6 py-4">{% for cat,msg in messages %}<div class="p-4 rounded-lg mb-2 {{ 'bg-green-900 text-green-200' if cat=='success' else ('bg-yellow-900 text-yellow-200' if cat=='warning' else 'bg-red-900 text-red-200') }}">{{ msg }}</div>{% endfor %}</div>
{% endif %}{% endwith %}
<div class="p-6">{% block content %}{% endblock %}</div>
</main>
</div>
{% block extra_scripts %}{% endblock %}
</body></html>""",

'index.html': """{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block page_title %}Dashboard{% endblock %}
{% block content %}
<div x-data="{stats:{total_files:0}}" x-init="fetch('/api/stats').then(r=>r.json()).then(d=>stats=d)">
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
<div class="card p-6"><p class="text-gray-400 text-sm">Courses</p><p class="text-3xl font-bold">{{ total_courses }}</p></div>
<div class="card p-6"><p class="text-gray-400 text-sm">Available</p><p class="text-3xl font-bold text-green-400">{{ available_courses }}</p></div>
<div class="card p-6"><p class="text-gray-400 text-sm">Unavailable</p><p class="text-3xl font-bold text-orange-400">{{ total_courses - available_courses }}</p></div>
<div class="card p-6"><p class="text-gray-400 text-sm">Files</p><p class="text-3xl font-bold" x-text="stats.total_files">0</p></div>
</div>
{% if continue_watching %}
<div class="mb-8"><div class="flex items-center justify-between mb-4"><h2 class="text-2xl font-bold">Continue Watching</h2>
<a href="{{ url_for('main.continue_watching_page') }}" class="text-blue-400 hover:text-blue-300 text-sm">See All <i class="fas fa-arrow-right ml-1"></i></a></div>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">{% for p in continue_watching %}
<div class="card overflow-hidden hover:ring-2 ring-blue-500 transition-all">
<div class="relative">
{% if p.file.thumbnail %}
<img src="{{ p.file.thumbnail }}" class="w-full h-40 object-cover">
{% elif p.file.file_type == 'video' %}
<div class="w-full h-40 bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center">
<i class="fas fa-play-circle text-5xl text-blue-300"></i></div>
{% elif p.file.file_type == 'audio' %}
{% if p.file.course.thumbnail %}
<img src="{{ p.file.course.thumbnail }}" class="w-full h-40 object-cover">
{% else %}
<div class="w-full h-40 bg-gradient-to-br from-purple-900 to-purple-700 flex items-center justify-center">
<i class="fas fa-music text-5xl text-purple-300"></i></div>
{% endif %}
{% else %}
<div class="w-full h-40 bg-gray-800 flex items-center justify-center">
<i class="fas fa-file text-5xl text-gray-500"></i></div>
{% endif %}
{% if p.file.duration %}
<div class="absolute bottom-2 right-2 bg-black/75 px-2 py-1 rounded text-xs font-medium">
{{ fmt_dur(p.file.duration) }}</div>
{% endif %}
<div class="absolute bottom-0 left-0 right-0 h-1 bg-gray-900/75">
<div class="h-full bg-blue-500" style="width:{{ (p.current_time/p.file.duration*100)|int if p.file.duration else 0 }}%"></div></div>
</div>
<div class="p-3">
<h3 class="font-semibold truncate text-sm mb-1">{{ p.file.file_name }}</h3>
<p class="text-xs text-gray-400 mb-2"><i class="fas fa-book mr-1"></i>{{ p.file.course.display_name }}</p>
<a href="{{ url_for('player.play',file_hash=p.file.file_hash) }}" class="btn-primary w-full text-center block text-xs py-2">
<i class="fas fa-play mr-1"></i>Resume</a>
</div></div>
{% endfor %}</div></div>{% endif %}
{% if recent_courses %}
<div class="mb-8"><h2 class="text-2xl font-bold mb-4">Recent</h2>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">{% for c in recent_courses %}
<div class="card overflow-hidden"><div class="aspect-video bg-gradient-to-br from-blue-600 to-purple-600 relative">
{% if c.thumbnail %}<img src="{{ c.thumbnail }}" class="absolute inset-0 w-full h-full object-cover">{% else %}<div class="absolute inset-0 flex items-center justify-center"><i class="fas fa-book-open text-6xl text-white opacity-50"></i></div>{% endif %}
<div class="absolute top-2 right-2"><span class="badge {{ 'badge-success' if c.is_available else 'badge-warning' }}">{{ 'Available' if c.is_available else 'Unavailable' }}</span></div></div>
<div class="p-4"><h3 class="font-semibold">{{ c.display_name }}</h3><p class="text-sm text-gray-400 mt-1">{{ c.total_files }} files</p>
<a href="{{ url_for('courses.detail',course_id=c.id) }}" class="btn-secondary w-full text-center block mt-3">Open</a></div></div>
{% endfor %}</div></div>{% endif %}
<div class="card p-6"><h2 class="text-xl font-bold mb-4">Quick Actions</h2>
<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
<a href="{{ url_for('courses.add_course') }}" class="btn-primary text-center p-4"><i class="fas fa-plus-circle text-2xl mb-2"></i><p>Add Course</p></a>
<a href="{{ url_for('settings.index') }}" class="btn-secondary text-center p-4"><i class="fas fa-cog text-2xl mb-2"></i><p>Settings</p></a>
<a href="{{ url_for('courses.index') }}" class="btn-secondary text-center p-4"><i class="fas fa-th-large text-2xl mb-2"></i><p>Browse</p></a>
</div></div></div>
{% endblock %}""",

'continue_watching.html': """{% extends "base.html" %}
{% block title %}Continue Watching{% endblock %}
{% block page_title %}Continue Watching{% endblock %}
{% block content %}
{% if items %}
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">{% for p in items %}
<div class="card overflow-hidden hover:ring-2 ring-blue-500 transition-all">
<div class="relative">
{% if p.file.thumbnail %}
<img src="{{ p.file.thumbnail }}" class="w-full h-40 object-cover">
{% elif p.file.file_type == 'video' %}
<div class="w-full h-40 bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center">
<i class="fas fa-play-circle text-5xl text-blue-300"></i></div>
{% elif p.file.file_type == 'audio' %}
{% if p.file.course.thumbnail %}
<img src="{{ p.file.course.thumbnail }}" class="w-full h-40 object-cover">
{% else %}
<div class="w-full h-40 bg-gradient-to-br from-purple-900 to-purple-700 flex items-center justify-center">
<i class="fas fa-music text-5xl text-purple-300"></i></div>
{% endif %}
{% else %}
<div class="w-full h-40 bg-gray-800 flex items-center justify-center">
<i class="fas fa-file text-5xl text-gray-500"></i></div>
{% endif %}
{% if p.file.duration %}
<div class="absolute bottom-2 right-2 bg-black/75 px-2 py-1 rounded text-xs font-medium">
{{ fmt_dur(p.file.duration) }}</div>
{% endif %}
<div class="absolute bottom-0 left-0 right-0 h-1 bg-gray-900/75">
<div class="h-full bg-blue-500" style="width:{{ (p.current_time/p.file.duration*100)|int if p.file.duration else 0 }}%"></div></div>
</div>
<div class="p-3">
<h3 class="font-semibold truncate text-sm mb-1">{{ p.file.file_name }}</h3>
<p class="text-xs text-gray-400 mb-2"><i class="fas fa-book mr-1"></i>{{ p.file.course.display_name }}</p>
<a href="{{ url_for('player.play',file_hash=p.file.file_hash) }}" class="btn-primary w-full text-center block text-xs py-2">
<i class="fas fa-play mr-1"></i>Resume</a>
</div></div>
{% endfor %}</div>
{% else %}<div class="card p-12 text-center"><i class="fas fa-history text-6xl text-gray-600 mb-4"></i><h3>Nothing in progress</h3></div>{% endif %}
{% endblock %}""",

'courses.html': """{% extends "base.html" %}
{% block title %}Courses{% endblock %}
{% block page_title %}{{ 'Available' if filter_type=='available' else ('Unavailable' if filter_type=='unavailable' else 'All') }} Courses{% endblock %}
{% block content %}
<div x-data="coursesPage()">
<div class="flex items-center justify-between mb-6">
<div class="bg-gray-800 rounded-lg p-1 flex">
<a href="{{ url_for('courses.index') }}?filter=all" class="px-4 py-2 rounded {{ 'bg-blue-600' if filter_type=='all' else '' }}">All</a>
<a href="{{ url_for('courses.available') }}" class="px-4 py-2 rounded {{ 'bg-blue-600' if filter_type=='available' else '' }}">Available</a>
<a href="{{ url_for('courses.unavailable') }}" class="px-4 py-2 rounded {{ 'bg-blue-600' if filter_type=='unavailable' else '' }}">Unavailable</a></div>
<div class="flex items-center space-x-3">
<div class="bg-gray-800 rounded-lg p-1 flex">
<a href="?view=grid" class="px-3 py-2 rounded {{ 'bg-gray-700' if view_mode=='grid' else '' }}"><i class="fas fa-th"></i></a>
<a href="?view=list" class="px-3 py-2 rounded {{ 'bg-gray-700' if view_mode=='list' else '' }}"><i class="fas fa-list"></i></a></div>
<button @click="showModal=true" class="btn-primary"><i class="fas fa-plus mr-2"></i>Add Course</button></div></div>
{% if courses %}
{% if view_mode=='grid' %}
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">{% for c in courses %}
<div class="card overflow-hidden group"><div class="aspect-video bg-gradient-to-br from-blue-600 to-purple-600 relative">
{% if c.thumbnail %}<img src="{{ c.thumbnail }}" class="absolute inset-0 w-full h-full object-cover">{% endif %}
<div class="absolute top-2 right-2"><span class="badge {{ 'badge-success' if c.is_available else 'badge-warning' }}">{{ 'Available' if c.is_available else 'Unavailable' }}</span></div>
<div class="absolute inset-0 bg-black bg-opacity-75 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2">
<a href="{{ url_for('courses.detail',course_id=c.id) }}" class="btn-primary"><i class="fas fa-folder-open"></i></a>
<button @click="rescan({{ c.id }})" class="btn-secondary"><i class="fas fa-sync"></i></button>
<button @click="del({{ c.id }},'{{ c.display_name }}')" class="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded"><i class="fas fa-trash"></i></button></div></div>
<div class="p-4"><h3 class="font-semibold text-lg truncate">{{ c.display_name }}</h3>
<span class="text-sm text-gray-400">{{ c.total_files }} files</span>
<a href="{{ url_for('courses.detail',course_id=c.id) }}" class="btn-primary w-full text-center block mt-3">Open</a></div></div>
{% endfor %}</div>
{% else %}
<div class="card overflow-hidden"><table class="w-full"><thead class="bg-gray-800"><tr><th class="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Name</th><th class="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Path</th><th class="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Files</th><th class="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Actions</th></tr></thead>
<tbody class="divide-y divide-gray-700">{% for c in courses %}
<tr class="hover:bg-gray-800"><td class="px-6 py-4 font-medium">{{ c.display_name }}</td><td class="px-6 py-4 text-sm text-gray-400">{{ c.root_path }}</td><td class="px-6 py-4">{{ c.total_files }}</td>
<td class="px-6 py-4 flex space-x-2"><a href="{{ url_for('courses.detail',course_id=c.id) }}" class="text-blue-400"><i class="fas fa-folder-open"></i></a>
<button @click="rescan({{ c.id }})" class="text-green-400"><i class="fas fa-sync"></i></button>
<button @click="del({{ c.id }},'{{ c.display_name }}')" class="text-red-400"><i class="fas fa-trash"></i></button></td></tr>
{% endfor %}</tbody></table></div>{% endif %}
{% else %}<div class="card p-12 text-center"><i class="fas fa-folder-open text-6xl text-gray-600 mb-4"></i><h3 class="text-xl font-semibold mb-2">No courses</h3><button @click="showModal=true" class="btn-primary"><i class="fas fa-plus mr-2"></i>Add Course</button></div>{% endif %}
<div x-show="showModal" x-cloak class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 overflow-y-auto" @click.self="showModal=false">
<div class="bg-gray-800 rounded-lg p-6 w-full max-w-2xl my-8"><h2 class="text-2xl font-bold mb-4">Add Course</h2>
<form @submit.prevent="add()">
<div class="mb-4"><label class="block text-sm font-medium mb-2">Name</label>
<input type="text" x-model="name" class="input-field" required></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Path</label>
<input type="text" x-model="path" class="input-field" required></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Creators</label>
<div class="relative"><input type="text" x-model="creatorSearch" @input="searchCreators()" @focus="creatorDropdown=true" @click.away="creatorDropdown=false" placeholder="Type to search or add..." class="input-field">
<div x-show="creatorDropdown" x-cloak class="absolute z-10 w-full mt-1 bg-gray-700 rounded-lg shadow-xl max-h-48 overflow-y-auto">
<template x-for="c in filteredCreators" :key="c.id">
<div @click="addCreator(c)" class="p-2 hover:bg-gray-600 cursor-pointer flex items-center justify-between">
<span x-text="c.name"></span><i class="fas fa-plus text-xs"></i></div></template>
<div x-show="creatorSearch&&filteredCreators.length===0" @click="addNewCreator()" class="p-2 hover:bg-gray-600 cursor-pointer text-blue-400">
<i class="fas fa-plus mr-2"></i>Create "<span x-text="creatorSearch"></span>"</div></div></div>
<div class="flex flex-wrap gap-2 mt-2">
<template x-for="(c,idx) in selectedCreators" :key="idx">
<span class="bg-purple-600 px-3 py-1 rounded-full text-sm flex items-center space-x-2">
<span x-text="c.name"></span><button type="button" @click="selectedCreators.splice(idx,1)" class="hover:text-red-300"><i class="fas fa-times text-xs"></i></button></span></template></div></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Categories</label>
<div class="relative"><input type="text" x-model="categorySearch" @input="searchCategories()" @focus="categoryDropdown=true" @click.away="categoryDropdown=false" placeholder="Type to search or add..." class="input-field">
<div x-show="categoryDropdown" x-cloak class="absolute z-10 w-full mt-1 bg-gray-700 rounded-lg shadow-xl max-h-48 overflow-y-auto">
<template x-for="c in filteredCategories" :key="c.id">
<div @click="addCategory(c)" class="p-2 hover:bg-gray-600 cursor-pointer flex items-center justify-between">
<span x-text="c.name"></span><i class="fas fa-plus text-xs"></i></div></template>
<div x-show="categorySearch&&filteredCategories.length===0" @click="addNewCategory()" class="p-2 hover:bg-gray-600 cursor-pointer text-blue-400">
<i class="fas fa-plus mr-2"></i>Create "<span x-text="categorySearch"></span>"</div></div></div>
<div class="flex flex-wrap gap-2 mt-2">
<template x-for="(c,idx) in selectedCategories" :key="idx">
<span class="bg-blue-600 px-3 py-1 rounded-full text-sm flex items-center space-x-2">
<span x-text="c.name"></span><button type="button" @click="selectedCategories.splice(idx,1)" class="hover:text-red-300"><i class="fas fa-times text-xs"></i></button></span></template></div></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Tags</label>
<div class="relative"><input type="text" x-model="tagSearch" @input="searchTags()" @focus="tagDropdown=true" @click.away="tagDropdown=false" placeholder="Type to search or add..." class="input-field">
<div x-show="tagDropdown" x-cloak class="absolute z-10 w-full mt-1 bg-gray-700 rounded-lg shadow-xl max-h-48 overflow-y-auto">
<template x-for="t in filteredTags" :key="t.id">
<div @click="addTag(t)" class="p-2 hover:bg-gray-600 cursor-pointer flex items-center justify-between">
<span x-text="t.name"></span><i class="fas fa-plus text-xs"></i></div></template>
<div x-show="tagSearch&&filteredTags.length===0" @click="addNewTag()" class="p-2 hover:bg-gray-600 cursor-pointer text-blue-400">
<i class="fas fa-plus mr-2"></i>Create "<span x-text="tagSearch"></span>"</div></div></div>
<div class="flex flex-wrap gap-2 mt-2">
<template x-for="(t,idx) in selectedTags" :key="idx">
<span class="bg-green-600 px-3 py-1 rounded-full text-sm flex items-center space-x-2">
<span x-text="t.name"></span><button type="button" @click="selectedTags.splice(idx,1)" class="hover:text-red-300"><i class="fas fa-times text-xs"></i></button></span></template></div></div>
<div class="flex justify-end space-x-3"><button type="button" @click="showModal=false" class="btn-secondary">Cancel</button>
<button type="submit" class="btn-primary" :disabled="busy"><span x-text="busy?'Adding...':'Add'"></span></button></div></form></div></div>
</div>
<script>
function coursesPage(){return{
showModal:{{ 'true' if show_add_modal else 'false' }},busy:false,name:'',path:'',
allCreators:[],allCategories:[],allTags:[],
creatorSearch:'',categorySearch:'',tagSearch:'',
creatorDropdown:false,categoryDropdown:false,tagDropdown:false,
selectedCreators:[],selectedCategories:[],selectedTags:[],
filteredCreators:[],filteredCategories:[],filteredTags:[],
init(){
fetch('/creators/api/all').then(r=>r.json()).then(d=>this.allCreators=d);
fetch('/categories/api/all').then(r=>r.json()).then(d=>this.allCategories=d);
fetch('/tags/api/all').then(r=>r.json()).then(d=>this.allTags=d);
},
searchCreators(){this.filteredCreators=this.allCreators.filter(c=>c.name.toLowerCase().includes(this.creatorSearch.toLowerCase())&&!this.selectedCreators.find(s=>s.id===c.id))},
searchCategories(){this.filteredCategories=this.allCategories.filter(c=>c.name.toLowerCase().includes(this.categorySearch.toLowerCase())&&!this.selectedCategories.find(s=>s.id===c.id))},
searchTags(){this.filteredTags=this.allTags.filter(t=>t.name.toLowerCase().includes(this.tagSearch.toLowerCase())&&!this.selectedTags.find(s=>s.id===t.id))},
addCreator(c){this.selectedCreators.push(c);this.creatorSearch='';this.creatorDropdown=false},
addCategory(c){this.selectedCategories.push(c);this.categorySearch='';this.categoryDropdown=false},
addTag(t){this.selectedTags.push(t);this.tagSearch='';this.tagDropdown=false},
addNewCreator(){fetch('/creators/api/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:this.creatorSearch})}).then(r=>r.json()).then(d=>{if(d.error)alert(d.error);else{this.allCreators.push(d);this.addCreator(d)}})},
addNewCategory(){fetch('/categories/api/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:this.categorySearch})}).then(r=>r.json()).then(d=>{if(d.error)alert(d.error);else{this.allCategories.push(d);this.addCategory(d)}})},
addNewTag(){fetch('/tags/api/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:this.tagSearch})}).then(r=>r.json()).then(d=>{if(d.error)alert(d.error);else{this.allTags.push(d);this.addTag(d)}})},
add(){this.busy=true;
const data={display_name:this.name,root_path:this.path,
creator_ids:this.selectedCreators.map(c=>c.id),
category_ids:this.selectedCategories.map(c=>c.id),
tag_ids:this.selectedTags.map(t=>t.id)};
fetch("{{ url_for('courses.add_course') }}",{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).then(r=>r.json()).then(d=>{if(d.course_id)location.href='/courses/'+d.course_id;else alert(d.error||'Error')}).catch(e=>alert(e.message)).finally(()=>this.busy=false)},
rescan(id){if(!confirm('Rescan?'))return;fetch('/courses/'+id+'/rescan',{method:'POST'}).then(r=>r.json()).then(d=>{alert(d.files_count+' files');location.reload()})},
del(id,n){if(!confirm('Delete "'+n+'"?'))return;fetch('/courses/'+id+'/delete',{method:'POST'}).then(r=>{if(r.ok)location.reload()})}
}}
</script>
{% endblock %}""",

'course_detail.html': """{% extends "base.html" %}
{% block title %}{{ course.display_name }}{% endblock %}
{% block page_title %}{{ course.display_name }}{% endblock %}
{% block content %}
{% macro file_icon(ft) %}{{ 'fa-video text-blue-400' if ft=='video' else ('fa-music text-purple-400' if ft=='audio' else ('fa-file-pdf text-red-400' if ft=='pdf' else ('fa-image text-green-400' if ft=='image' else ('fa-book text-yellow-400' if ft=='epub' else 'fa-file text-gray-400')))) }}{% endmacro %}
{% macro render_file_card(file, show_course=False) %}
<div class="card p-3 mb-2 hover:bg-gray-800/50 transition-all">
<div class="flex items-start space-x-3">
<div class="relative flex-shrink-0">
{% if file.thumbnail %}
<img src="{{ file.thumbnail }}" class="w-32 h-20 object-cover rounded">
{% elif file.file_type == 'video' %}
<div class="w-32 h-20 bg-gradient-to-br from-blue-900 to-blue-700 rounded flex items-center justify-center">
<i class="fas fa-video text-2xl text-blue-300"></i></div>
{% elif file.file_type == 'audio' %}
<div class="w-32 h-20 bg-gradient-to-br from-purple-900 to-purple-700 rounded flex items-center justify-center">
<i class="fas fa-music text-2xl text-purple-300"></i></div>
{% else %}
<div class="w-32 h-20 bg-gray-700 rounded flex items-center justify-center">
<i class="fas {{ file_icon(file.file_type) }} text-2xl"></i></div>
{% endif %}
{% if file.duration %}
<div class="absolute bottom-1 right-1 bg-black/75 px-1.5 py-0.5 rounded text-xs font-medium">
{{ fmt_dur(file.duration) }}</div>
{% endif %}
{% if file.id in watched_ids %}
<div class="absolute top-1 right-1 bg-green-600 rounded-full p-1">
<i class="fas fa-check text-xs"></i></div>
{% elif progress_map.get(file.id) and progress_map.get(file.id).current_time > 0 %}
<div class="absolute bottom-0 left-0 right-0 h-1 bg-gray-900/75 rounded-b">
<div class="h-full bg-blue-500 rounded-b" style="width:{{ (progress_map.get(file.id).current_time / file.duration * 100)|int if file.duration else 0 }}%"></div></div>
{% endif %}
</div>
<div class="flex-1 min-w-0">
<h4 class="font-medium truncate text-sm" :id="'fn-{{ file.file_hash }}'">{{ file.display_name or file.file_name }}</h4>
<div class="flex items-center space-x-2 mt-1 text-xs text-gray-400">
<span><i class="fas fa-hdd mr-1"></i>{{ (file.file_size/1024/1024)|round(1) }} MB</span>
{% if file.file_extension %}<span class="px-1.5 py-0.5 bg-gray-700 rounded">{{ file.file_extension[1:].upper() }}</span>{% endif %}
{% if file.video_quality %}<span class="px-1.5 py-0.5 bg-blue-900 rounded">{{ file.video_quality }}</span>{% endif %}
</div>
{% if show_course %}
<p class="text-xs text-gray-500 mt-1"><i class="fas fa-book mr-1"></i>{{ file.course.display_name }}</p>
{% endif %}
</div>
<div class="flex items-center space-x-1 flex-shrink-0">
<button @click="renameF('{{ file.file_hash }}','{{ (file.display_name or file.file_name)|e }}')" class="text-gray-500 hover:text-blue-400 px-2 py-1 rounded" title="Rename"><i class="fas fa-pen text-xs"></i></button>
<button @click="markW('{{ file.file_hash }}',$event)" class="{{ 'text-green-400' if file.id in watched_ids else 'text-gray-500 hover:text-gray-300' }} px-2 py-1 rounded" title="{{ 'Watched' if file.id in watched_ids else 'Mark watched' }}"><i class="fas fa-eye text-xs"></i></button>
{% if file.file_type in ['video','audio','pdf','image','epub'] %}
<a href="{{ url_for('player.play',file_hash=file.file_hash) }}" class="btn-primary text-xs px-3 py-1">
<i class="fas fa-play mr-1"></i>{{ 'View' if file.file_type in ('pdf','image') else 'Play' }}</a>
{% endif %}
</div></div></div>
{% endmacro %}
{% macro render_folder(node, depth) %}
<div class="{{ 'ml-4 pl-3 border-l-2 border-gray-700' if depth > 0 else '' }}">
<div @click="toggle('{{ node.path }}')" class="flex items-center justify-between p-2 cursor-pointer hover:bg-gray-800 rounded">
<div class="flex items-center space-x-3">
<i class="fas transition-transform text-xs" :class="isOpen('{{ node.path }}')?'fa-chevron-down':'fa-chevron-right'"></i>
<i class="fas fa-folder text-yellow-400"></i>
<span class="font-semibold">{{ node.name }}</span>
<span class="text-xs text-gray-500">{{ node.file_count }}f{% if node.total_duration %} · {{ fmt_dur_h(node.total_duration) }}{% endif %}{% if node.watched_duration > 0 %}{% if node.watched_duration >= node.total_duration %} · ✓{% else %} · {{ fmt_dur_h(node.total_duration - node.watched_duration) }} left{% endif %}{% endif %}</span>
</div></div>
{% if node.watched_duration > 0 and node.total_duration > 0 %}
<div x-show="isOpen('{{ node.path }}')" x-cloak class="px-3 pb-1"><div class="w-full h-1 bg-gray-700 rounded-full overflow-hidden"><div class="h-full rounded-full transition-all" :class="isOpen('{{ node.path }}')?'':'hidden'" style="width:{{ (node.watched_duration/node.total_duration*100)|int }}%;background:{% if node.watched_duration >= node.total_duration %}#10b981{% else %}#3b82f6{% endif %}"></div></div></div>{% endif %}
<div x-show="isOpen('{{ node.path }}')" x-cloak>
{% for child in node.children %}{{ render_folder(child, depth+1) }}{% endfor %}
{% for file in node.files %}
<div class="{{ 'ml-2' if depth > 0 }}" :class="isOpen('{{ node.path }}')?'':'hidden'">
{{ render_file_card(file) }}
</div>
{% endfor %}
</div></div>
{% endmacro %}
<div x-data="courseDetail()">
<div class="grid grid-cols-12 gap-6">
<!-- LEFT: Video List -->
<div class="col-span-12 lg:col-span-8 space-y-4">
<div class="card p-4">
<div class="flex items-center justify-between mb-4">
<h2 class="text-xl font-bold"><i class="fas fa-list mr-2"></i>Content</h2>
<div class="flex space-x-2">
<button @click="toggleAll()" class="btn-secondary text-sm">
<i class="fas" :class="expandAll?'fa-compress':'fa-expand'"></i>
<span x-text="expandAll?' Collapse':' Expand'"></span>
</button>
</div>
</div>
{# Root-level files #}
{% for file in tree.files %}
{{ render_file_card(file) }}
{% endfor %}
{# Nested folders #}
{% for child in tree.children %}{{ render_folder(child, 0) }}{% endfor %}
{% if not tree.files and not tree.children %}
<div class="text-center py-12">
<i class="fas fa-folder-open text-6xl text-gray-600 mb-4"></i>
<h3 class="text-xl font-semibold mb-2">No files</h3>
<button @click="rescan()" class="btn-primary"><i class="fas fa-sync mr-2"></i>Rescan</button>
</div>
{% endif %}
</div>
</div>

<!-- RIGHT: Course Info -->
<div class="col-span-12 lg:col-span-4 space-y-4">
<!-- Course Header -->
<div class="card overflow-hidden">
<div class="relative group">
{% if course.thumbnail %}
<img src="{{ course.thumbnail }}" class="w-full h-48 object-cover">
{% else %}
<div class="w-full h-48 bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center">
<i class="fas fa-graduation-cap text-6xl text-white opacity-50"></i>
</div>
{% endif %}
<button @click="showThumb=true" class="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
<i class="fas fa-camera text-white text-3xl"></i>
</button>
</div>
<div class="p-4">
<div class="flex items-center justify-between mb-2">
<h1 class="text-2xl font-bold">{{ course.display_name }}</h1>
<span class="badge {{ 'badge-success' if course.is_available else 'badge-warning' }}">
{{ 'Available' if course.is_available else 'Unavailable' }}
</span>
</div>
<p class="text-xs text-gray-400 mb-3">{{ course.root_path }}</p>
<div class="flex items-center space-x-4 text-sm text-gray-400 mb-3">
<span><i class="fas fa-file mr-1"></i>{{ tree.file_count }}</span>
{% if tree.total_duration %}
<span><i class="fas fa-clock mr-1"></i>{{ fmt_dur_h(tree.total_duration) }}</span>
{% endif %}
</div>
{% if tree.total_duration > 0 %}
<div class="mb-3">
<div class="flex justify-between text-xs text-gray-400 mb-1">
<span>Progress</span>
<span>{{ (tree.watched_duration/tree.total_duration*100)|int }}%</span>
</div>
<div class="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
<div class="h-full bg-blue-500 rounded-full" style="width:{{ (tree.watched_duration/tree.total_duration*100)|int }}%"></div>
</div>
</div>
{% endif %}
<!-- Creators/Categories/Tags -->
{% if course.creators %}
<div class="mb-3">
<p class="text-xs text-gray-400 mb-1">Creators</p>
<div class="flex flex-wrap gap-1">
{% for creator in course.creators %}
<a href="{{ url_for('creators.detail', creator_id=creator.id) }}" class="text-xs px-2 py-1 bg-purple-600 rounded hover:bg-purple-500">
{{ creator.name }}
</a>
{% endfor %}
</div>
</div>
{% endif %}
{% if course.categories %}
<div class="mb-3">
<p class="text-xs text-gray-400 mb-1">Categories</p>
<div class="flex flex-wrap gap-1">
{% for category in course.categories %}
<a href="{{ url_for('categories.detail', category_id=category.id) }}" class="text-xs px-2 py-1 bg-blue-600 rounded hover:bg-blue-500">
{{ category.name }}
</a>
{% endfor %}
</div>
</div>
{% endif %}
{% if course.tags %}
<div class="mb-3">
<p class="text-xs text-gray-400 mb-1">Tags</p>
<div class="flex flex-wrap gap-1">
{% for tag in course.tags %}
<a href="{{ url_for('tags.detail', tag_id=tag.id) }}" class="text-xs px-2 py-1 bg-green-600 rounded hover:bg-green-500">
{{ tag.name }}
</a>
{% endfor %}
</div>
</div>
{% endif %}
<div class="flex space-x-2 pt-3 border-t border-gray-700">
<button @click="showEditMeta=true" class="btn-primary text-xs flex-1">
<i class="fas fa-edit mr-1"></i>Edit
</button>
<button @click="rescan()" class="btn-secondary text-xs flex-1">
<i class="fas fa-sync mr-1"></i>Rescan
</button>
<a href="{{ url_for('settings.course_settings',course_id=course.id) }}" class="btn-secondary text-xs flex-1 text-center">
<i class="fas fa-cog mr-1"></i>Settings
</a>
</div>
</div>
</div>

<!-- Description -->
<div class="card p-4">
<div class="flex items-center justify-between mb-3">
<h3 class="font-bold"><i class="fas fa-info-circle mr-2"></i>Description</h3>
<button @click="showEditDesc=true" class="text-blue-400 hover:text-blue-300 text-xs">
<i class="fas fa-edit"></i>
</button>
</div>
{% if course.description %}
<div class="prose prose-invert prose-sm max-w-none">{{ course.description|safe }}</div>
{% else %}
<p class="text-gray-500 text-sm italic">No description</p>
{% endif %}
</div>
</div>
</div>

<!-- Modals -->
<div x-show="showThumb" x-cloak class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" @click.self="showThumb=false">
<div class="bg-gray-800 rounded-lg p-6 w-full max-w-md"><h2 class="text-xl font-bold mb-4">Thumbnail</h2>
<input type="text" x-model="thumb" class="input-field mb-4" placeholder="Path or URL">
<div class="flex justify-end space-x-3"><button @click="showThumb=false" class="btn-secondary">Cancel</button><button @click="saveThumb()" class="btn-primary">Save</button></div></div></div>

<div x-show="showEditDesc" x-cloak class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 overflow-y-auto" @click.self="showEditDesc=false">
<div class="bg-gray-800 rounded-lg p-6 w-full max-w-3xl my-8">
<h2 class="text-xl font-bold mb-4">Edit Description</h2>
<textarea x-model="desc" class="input-field h-64 resize-none font-mono text-sm mb-4" placeholder="HTML content..."></textarea>
<div class="flex justify-end space-x-3">
<button @click="showEditDesc=false" class="btn-secondary">Cancel</button>
<button @click="saveDesc()" class="btn-primary">Save</button>
</div>
</div>
</div>

<div x-show="showEditMeta" x-cloak class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 overflow-y-auto" @click.self="showEditMeta=false">
<div class="bg-gray-800 rounded-lg p-6 w-full max-w-2xl my-8">
<h2 class="text-xl font-bold mb-4">Edit Metadata</h2>
<form @submit.prevent="saveMeta()">
<div class="mb-4"><label class="block text-sm font-medium mb-2">Creators</label>
<div class="relative"><input type="text" x-model="creatorSearch" @input="searchCreators()" @focus="creatorDropdown=true" @click.away="creatorDropdown=false" placeholder="Type to search..." class="input-field">
<div x-show="creatorDropdown" x-cloak class="absolute z-10 w-full mt-1 bg-gray-700 rounded-lg shadow-xl max-h-48 overflow-y-auto">
<template x-for="c in filteredCreators" :key="c.id">
<div @click="addCreator(c)" class="p-2 hover:bg-gray-600 cursor-pointer">
<span x-text="c.name"></span></div></template>
<div x-show="creatorSearch&&filteredCreators.length===0" @click="addNewCreator()" class="p-2 hover:bg-gray-600 cursor-pointer text-blue-400">
<i class="fas fa-plus mr-2"></i>Create "<span x-text="creatorSearch"></span>"</div></div></div>
<div class="flex flex-wrap gap-2 mt-2">
<template x-for="(c,idx) in selectedCreators" :key="idx">
<span class="bg-purple-600 px-3 py-1 rounded-full text-sm flex items-center space-x-2">
<span x-text="c.name"></span><button type="button" @click="selectedCreators.splice(idx,1)" class="hover:text-red-300"><i class="fas fa-times text-xs"></i></button></span></template></div></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Categories</label>
<div class="relative"><input type="text" x-model="categorySearch" @input="searchCategories()" @focus="categoryDropdown=true" @click.away="categoryDropdown=false" placeholder="Type to search..." class="input-field">
<div x-show="categoryDropdown" x-cloak class="absolute z-10 w-full mt-1 bg-gray-700 rounded-lg shadow-xl max-h-48 overflow-y-auto">
<template x-for="c in filteredCategories" :key="c.id">
<div @click="addCategory(c)" class="p-2 hover:bg-gray-600 cursor-pointer">
<span x-text="c.name"></span></div></template>
<div x-show="categorySearch&&filteredCategories.length===0" @click="addNewCategory()" class="p-2 hover:bg-gray-600 cursor-pointer text-blue-400">
<i class="fas fa-plus mr-2"></i>Create "<span x-text="categorySearch"></span>"</div></div></div>
<div class="flex flex-wrap gap-2 mt-2">
<template x-for="(c,idx) in selectedCategories" :key="idx">
<span class="bg-blue-600 px-3 py-1 rounded-full text-sm flex items-center space-x-2">
<span x-text="c.name"></span><button type="button" @click="selectedCategories.splice(idx,1)" class="hover:text-red-300"><i class="fas fa-times text-xs"></i></button></span></template></div></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Tags</label>
<div class="relative"><input type="text" x-model="tagSearch" @input="searchTags()" @focus="tagDropdown=true" @click.away="tagDropdown=false" placeholder="Type to search..." class="input-field">
<div x-show="tagDropdown" x-cloak class="absolute z-10 w-full mt-1 bg-gray-700 rounded-lg shadow-xl max-h-48 overflow-y-auto">
<template x-for="t in filteredTags" :key="t.id">
<div @click="addTag(t)" class="p-2 hover:bg-gray-600 cursor-pointer">
<span x-text="t.name"></span></div></template>
<div x-show="tagSearch&&filteredTags.length===0" @click="addNewTag()" class="p-2 hover:bg-gray-600 cursor-pointer text-blue-400">
<i class="fas fa-plus mr-2"></i>Create "<span x-text="tagSearch"></span>"</div></div></div>
<div class="flex flex-wrap gap-2 mt-2">
<template x-for="(t,idx) in selectedTags" :key="idx">
<span class="bg-green-600 px-3 py-1 rounded-full text-sm flex items-center space-x-2">
<span x-text="t.name"></span><button type="button" @click="selectedTags.splice(idx,1)" class="hover:text-red-300"><i class="fas fa-times text-xs"></i></button></span></template></div></div>
<div class="flex justify-end space-x-3 mt-6">
<button type="button" @click="showEditMeta=false" class="btn-secondary">Cancel</button>
<button type="submit" class="btn-primary">Save</button>
</div>
</form>
</div>
</div>
</div>
<script>
function courseDetail(){return{
showThumb:false,thumb:'{{ course.thumbnail or "" }}',
showEditDesc:false,desc:{{ course_description|tojson }},
showEditMeta:false,expandAll:true,overrides:{},
allCreators:[],allCategories:[],allTags:[],
creatorSearch:'',categorySearch:'',tagSearch:'',
creatorDropdown:false,categoryDropdown:false,tagDropdown:false,
selectedCreators:{{ course_creators_json|tojson }},
selectedCategories:{{ course_categories_json|tojson }},
selectedTags:{{ course_tags_json|tojson }},
filteredCreators:[],filteredCategories:[],filteredTags:[],
init(){
fetch('/creators/api/all').then(r=>r.json()).then(d=>this.allCreators=d);
fetch('/categories/api/all').then(r=>r.json()).then(d=>this.allCategories=d);
fetch('/tags/api/all').then(r=>r.json()).then(d=>this.allTags=d);
},
searchCreators(){this.filteredCreators=this.allCreators.filter(c=>c.name.toLowerCase().includes(this.creatorSearch.toLowerCase())&&!this.selectedCreators.find(s=>s.id===c.id))},
searchCategories(){this.filteredCategories=this.allCategories.filter(c=>c.name.toLowerCase().includes(this.categorySearch.toLowerCase())&&!this.selectedCategories.find(s=>s.id===c.id))},
searchTags(){this.filteredTags=this.allTags.filter(t=>t.name.toLowerCase().includes(this.tagSearch.toLowerCase())&&!this.selectedTags.find(s=>s.id===t.id))},
addCreator(c){this.selectedCreators.push(c);this.creatorSearch='';this.creatorDropdown=false},
addCategory(c){this.selectedCategories.push(c);this.categorySearch='';this.categoryDropdown=false},
addTag(t){this.selectedTags.push(t);this.tagSearch='';this.tagDropdown=false},
addNewCreator(){fetch('/creators/api/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:this.creatorSearch})}).then(r=>r.json()).then(d=>{if(d.error)alert(d.error);else{this.allCreators.push(d);this.addCreator(d)}})},
addNewCategory(){fetch('/categories/api/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:this.categorySearch})}).then(r=>r.json()).then(d=>{if(d.error)alert(d.error);else{this.allCategories.push(d);this.addCategory(d)}})},
addNewTag(){fetch('/tags/api/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:this.tagSearch})}).then(r=>r.json()).then(d=>{if(d.error)alert(d.error);else{this.allTags.push(d);this.addTag(d)}})},
isOpen(p){return this.overrides[p]!==undefined?this.overrides[p]:this.expandAll},
toggle(p){this.overrides[p]=!this.isOpen(p)},
toggleAll(){this.expandAll=!this.expandAll;this.overrides={}},
markW(hash,ev){const btn=ev.target.closest('button');const on=btn.classList.contains('text-green-400');
fetch('/api/mark-watched/'+hash,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({completed:!on})}).then(r=>{if(r.ok)location.reload()})},
renameF(hash,old){const nn=prompt('Rename file:',old);if(nn===null||nn.trim()==='')return;
fetch('/api/rename/'+hash,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:nn.trim()})}).then(r=>{if(r.ok)location.reload()})},
saveThumb(){fetch("{{ url_for('courses.update_thumbnail',course_id=course.id) }}",{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({thumbnail:this.thumb})}).then(r=>{if(r.ok)location.reload()})},
saveDesc(){fetch("{{ url_for('courses.update_metadata',course_id=course.id) }}",{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({description:this.desc})}).then(r=>{if(r.ok){this.showEditDesc=false;location.reload()}else alert('Failed')})},
saveMeta(){const data={creator_ids:this.selectedCreators.map(c=>c.id),category_ids:this.selectedCategories.map(c=>c.id),tag_ids:this.selectedTags.map(t=>t.id)};
fetch("{{ url_for('courses.update_metadata',course_id=course.id) }}",{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).then(r=>{if(r.ok){this.showEditMeta=false;location.reload()}else alert('Failed')})},
rescan(){if(!confirm('Rescan?'))return;fetch("{{ url_for('courses.rescan_course',course_id=course.id) }}",{method:'POST'}).then(r=>r.json()).then(d=>{alert(d.files_count+' files');location.reload()})}
}}
</script>
{% endblock %}""",

'course_settings.html': """{% extends "base.html" %}
{% block title %}{{ course.display_name }} Settings{% endblock %}
{% block page_title %}{{ course.display_name }} Settings{% endblock %}
{% block content %}
<div x-data="cs()" x-init="load()">
<div class="card p-6 max-w-4xl mx-auto"><div class="flex items-center justify-between mb-6"><h2 class="text-2xl font-bold"><i class="fas fa-cog mr-2"></i>Course Settings</h2>
<a href="{{ url_for('courses.detail',course_id=course.id) }}" class="btn-secondary"><i class="fas fa-arrow-left mr-2"></i>Back</a></div>
<form @submit.prevent="save()">
<div class="mb-6"><label class="block text-sm font-medium mb-2">Speed</label><select x-model="s.playback_speed" class="input-field"><option value="">Default</option><option value="0.5">0.5x</option><option value="0.75">0.75x</option><option value="1">1x</option><option value="1.5">1.5x</option><option value="2">2x</option><option value="3">3x</option><option value="4">4x</option></select></div>
<div class="mb-6"><label class="flex items-center space-x-2"><input type="checkbox" x-model="s.skip_silence_enabled"><span>Skip Silence</span></label>
<div x-show="s.skip_silence_enabled" class="ml-6 mt-3 space-y-3"><div><label class="block text-sm text-gray-400 mb-1">dB</label><input type="number" x-model.number="s.skip_silence_db_threshold" class="input-field" min="-60" max="0" step="5"></div>
<div><label class="block text-sm text-gray-400 mb-1">Min Duration</label><input type="number" x-model.number="s.skip_silence_min_duration" class="input-field" min="0.1" max="5" step="0.1"></div></div></div>
<div class="mb-6"><label class="flex items-center space-x-2"><input type="checkbox" x-model="s.subtitle_enabled"><span>Subtitles</span></label></div>
<div class="mb-6"><label class="flex items-center space-x-2"><input type="checkbox" x-model="s.rtl_enabled"><span>RTL</span></label></div>
<div class="flex justify-between"><button type="button" @click="reset()" class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded">Reset</button><button type="submit" class="btn-primary">Save</button></div>
</form></div></div>
<script>
function cs(){return{
s:{playback_speed:'',skip_silence_enabled:false,skip_silence_db_threshold:-40,skip_silence_min_duration:0.3,subtitle_enabled:false,rtl_enabled:false},
load(){fetch("{{ url_for('settings.course_settings',course_id=course.id) }}").then(r=>r.json()).then(d=>{for(let k in d)if(d[k]!==null)this.s[k]=d[k]}).catch(()=>{})},
save(){fetch("{{ url_for('settings.course_settings',course_id=course.id) }}",{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(this.s)}).then(r=>alert(r.ok?'Saved':'Failed')).catch(e=>alert(e.message))},
reset(){if(!confirm('Reset?'))return;fetch("{{ url_for('settings.reset_course_settings',course_id=course.id) }}",{method:'POST'}).then(()=>location.reload())}
}}
</script>
{% endblock %}""",

'player.html': """{% extends "base.html" %}
{% block title %}{{ file.display_name or file.file_name }}{% endblock %}
{% block page_title %}{{ course.display_name }}{% endblock %}
{% block extra_head %}
<style>
.theater-mode{position:fixed!important;inset:0;z-index:9999;background:#000}
.theater-mode .player-container{width:100vw!important;height:100vh!important;display:flex!important;align-items:center!important;justify-content:center!important;overflow:hidden;position:relative}
.theater-mode video{max-width:100vw!important;max-height:100vh!important;height:100vh!important;object-fit:contain!important}
.player-container{position:relative;background:#000}
@media(max-width:768px){
.player-container video{max-height:40vh}
.player-container .aspect-video{aspect-ratio:16/9}
}
.player-container.portrait-video video{max-height:60vh!important;width:auto!important;max-width:100%}
.player-container.portrait-video .aspect-video{aspect-ratio:9/16}
.player-controls{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(transparent,rgba(0,0,0,.85));padding:1rem;opacity:0;transition:opacity .3s}
.player-container:hover .player-controls{opacity:1}
.progress-bar{height:5px;background:rgba(255,255,255,.3);cursor:pointer}
.progress-bar-fill{height:100%;background:#3b82f6;position:relative}
.progress-bar-thumb{position:absolute;right:-8px;top:50%;transform:translateY(-50%);width:16px;height:16px;background:#fff;border-radius:50%;opacity:0;transition:opacity .2s}
.progress-bar:hover .progress-bar-thumb{opacity:1}
</style>
{% endblock %}
{% block content %}
<div x-data="pl()" x-init="init()" :class="{'theater-mode':theaterMode}">
<div class="grid grid-cols-12 gap-4 h-full">
<div :class="theaterMode?'col-span-12':'col-span-12 lg:col-span-8'" class="space-y-4">
<div class="player-container rounded-lg overflow-hidden" x-ref="playerContainer">
{% if file.file_type=='video' %}
<video x-ref="mediaPlayer" class="w-full" style="max-height:80vh;object-fit:contain" @timeupdate="updateProgress()" @loadedmetadata="onLoaded()" @ended="onEnded()">
<source src="{{ url_for('player.serve_file',file_hash=file.file_hash) }}">{% for sub in subtitle_files %}<track kind="subtitles" src="{{ url_for('player.serve_file',file_hash=sub.file_hash) }}" label="{{ sub.file_name }}">{% endfor %}</video>
{% elif file.file_type=='audio' %}
<div class="bg-gradient-to-br from-purple-900 to-blue-900 aspect-video flex items-center justify-center"><i class="fas fa-music text-9xl text-white opacity-50"></i></div>
<audio x-ref="mediaPlayer" @timeupdate="updateProgress()" @loadedmetadata="onLoaded()" @ended="onEnded()" class="hidden"><source src="{{ url_for('player.serve_file',file_hash=file.file_hash) }}"></audio>
{% elif file.file_type=='pdf' %}
<div class="bg-gray-900" style="min-height:600px">
<div class="flex justify-between items-center bg-gray-800 p-3"><button @click="pdfPage>1&&renderPage(pdfPage-1)" :disabled="pdfPage<=1" class="btn-secondary text-sm"><i class="fas fa-chevron-left"></i></button>
<span class="text-white text-sm"><span x-text="pdfPage"></span> / <span x-text="pdfCount"></span></span>
<button @click="pdfPage<pdfCount&&renderPage(pdfPage+1)" :disabled="pdfPage>=pdfCount" class="btn-secondary text-sm"><i class="fas fa-chevron-right"></i></button></div>
<div class="overflow-auto" style="max-height:800px" dir="{{ 'rtl' if settings.rtl_enabled else 'ltr' }}"><canvas x-ref="pdfCanvas" class="mx-auto"></canvas></div></div>
{% elif file.file_type=='epub' %}
<div style="min-height:600px;max-height:800px;overflow:auto" dir="{{ 'rtl' if settings.rtl_enabled else 'ltr' }}">
<div class="flex justify-between items-center bg-gray-800 p-3"><button @click="epubR&&epubR.prev()" class="btn-secondary text-sm"><i class="fas fa-chevron-left"></i></button>
<span class="text-white text-sm">EPUB</span><button @click="epubR&&epubR.next()" class="btn-secondary text-sm"><i class="fas fa-chevron-right"></i></button></div>
<div x-ref="epubViewer" style="height:700px;background:#fff"></div></div>
{% elif file.file_type=='image' %}
<img src="{{ url_for('player.serve_file',file_hash=file.file_hash) }}" class="w-full">
{% endif %}
{% if file.file_type in ['video','audio'] %}
<div class="player-controls">
<div class="progress-bar mb-3" @click="seekPos($event)" x-ref="progressBar"><div class="progress-bar-fill" :style="'width:'+(dur?cur/dur*100:0)+'%'"><div class="progress-bar-thumb"></div></div></div>
<div class="flex items-center justify-between text-white flex-wrap gap-y-2">
<div class="flex items-center space-x-2 sm:space-x-3">
<button x-show="!isFirst" @click="goPrev()" class="hover:text-blue-400 p-1 sm:p-0" title="Previous"><i class="fas fa-step-backward"></i></button>
<button @click="togglePlay()" class="hover:text-blue-400 p-1 sm:p-0"><i class="fas text-xl" :class="playing?'fa-pause':'fa-play'"></i></button>
<button x-show="!isLast" @click="goNext()" class="hover:text-blue-400 p-1 sm:p-0" title="Next"><i class="fas fa-step-forward"></i></button>
<button @click="toggleMute()" class="hover:text-blue-400 p-1 sm:p-0"><i class="fas" :class="muted||vol===0?'fa-volume-mute':vol<.5?'fa-volume-down':'fa-volume-up'"></i></button>
<input type="range" min="0" max="1" step="0.1" x-model.number="vol" @input="updateVol()" class="w-14 sm:w-20">
<span class="text-xs sm:text-sm" x-text="fmt(cur)+' / '+fmt(dur)"></span></div>
<div class="flex items-center space-x-2 sm:space-x-4">
<select x-model.number="speed" @change="$refs.mediaPlayer.playbackRate=speed" class="bg-gray-800 text-white px-1 sm:px-2 py-1 rounded text-sm">
<option value="0.5">0.5x</option><option value="0.75">0.75x</option><option value="1">1x</option>
<option value="1.5">1.5x</option><option value="2">2x</option><option value="3">3x</option><option value="4">4x</option></select>
<button @click="toggleSS()" :class="ssOn?'text-blue-400':'text-gray-400'" class="hover:text-blue-300 p-1" title="Skip Silence"><i class="fas fa-forward"></i></button>
{% if subtitle_files %}<button @click="toggleSubs()" class="hover:text-blue-400 p-1"><i class="fas fa-closed-captioning"></i></button>{% endif %}
<button @click="theaterMode=!theaterMode" class="hover:text-blue-400 p-1"><i class="fas" :class="theaterMode?'fa-compress':'fa-expand'"></i></button>
<button @click="fs()" class="hover:text-blue-400 p-1"><i class="fas fa-expand"></i></button></div></div></div>{% endif %}</div>
<div class="card p-4 sm:p-6" x-show="!theaterMode"><h2 class="text-lg sm:text-2xl font-bold mb-2">{{ file.display_name or file.file_name }}</h2>
<p class="text-gray-400 mb-4">{{ course.display_name }}</p>
<div class="flex items-center flex-wrap gap-2 mt-4">
<button @click="copyTs()" class="btn-secondary text-sm"><i class="fas fa-link mr-1"></i><span class="hidden sm:inline">Timestamp</span></button>
<button @click="showBM=true" class="btn-secondary text-sm"><i class="fas fa-bookmark mr-1"></i><span class="hidden sm:inline">Bookmark</span></button>
<button @click="showNote=true" class="btn-secondary text-sm"><i class="fas fa-sticky-note mr-1"></i><span class="hidden sm:inline">Note</span></button></div></div></div>
<div :class="theaterMode?'hidden':'col-span-12 lg:col-span-4'" class="space-y-4">
<div class="bg-gray-800 rounded-lg p-1 flex">
<button @click="tab='pl'" :class="tab==='pl'?'bg-blue-600':''" class="flex-1 px-4 py-2 rounded">Playlist</button>
<button @click="tab='notes'" :class="tab==='notes'?'bg-blue-600':''" class="flex-1 px-4 py-2 rounded">Notes</button>
<button @click="tab='bm'" :class="tab==='bm'?'bg-blue-600':''" class="flex-1 px-4 py-2 rounded">Bookmarks</button></div>
<div class="card p-4 max-h-[calc(100vh-300px)] overflow-y-auto">
<!-- PLAYLIST -->
<div x-show="tab==='pl'" x-cloak class="space-y-1">
<div class="bg-gray-800/60 rounded-lg p-2 mb-3 text-xs text-gray-400 flex items-center justify-between">
<span x-text="Object.keys(folderOpen).length+' folders, '+watchedHashes.length+'/'+allItems.filter(i=>i.type==='file').length+' watched'"></span>
<span x-show="_tree.total_duration>0" class="text-blue-400" x-text="fmtH(_tree.total_duration)+' total · '+fmtH(_tree.total_duration-_tree.watched_duration)+' left'"></span>
</div>
<div class="flex items-center justify-between mb-2">
<label class="flex items-center space-x-2 text-xs text-gray-400 cursor-pointer"><input type="checkbox" x-model="hideW" @change="saveHideW()"><span>Hide watched</span></label>
<button @click="togglePlAll()" class="text-xs text-blue-400 hover:text-blue-300" x-text="plAll?'Collapse':'Expand'"></button></div>
<template x-for="it in visItems" :key="it.type+(it.path||it.hash)">
<div :style="'padding-left:'+it.depth*16+'px'" class="group/item">
<!-- Folder -->
<template x-if="it.type==='folder'">
<div @click="toggleFolder(it.path)" class="flex items-center space-x-2 p-2 cursor-pointer hover:bg-gray-800 rounded-lg bg-gray-800/40">
<i class="fas text-xs transition-transform" :class="folderOpen[it.path]?'fa-chevron-down':'fa-chevron-right'"></i>
<i class="fas fa-folder text-yellow-400 text-xs"></i>
<span class="text-xs font-semibold flex-1" x-text="it.name"></span>
<span class="text-xs text-gray-500" x-text="it.file_count+' files'+(it.total_duration?' · '+fmtH(it.total_duration):'')"></span>
<span x-show="it.watched_duration>0&&it.watched_duration<it.total_duration" class="text-xs text-blue-400" x-text="fmtH(it.total_duration-it.watched_duration)+' left'"></span>
<span x-show="it.watched_duration>=it.total_duration&&it.total_duration>0" class="text-xs text-green-400">✓ done</span>
</div></template>
<!-- File -->
<template x-if="it.type==='file'">
<div :data-hash="it.hash" @click="location.href='/player/'+it.hash" class="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-700 cursor-pointer group/f" :class="{'bg-blue-600/30 ring-1 ring-blue-500':it.hash===curHash}">
<i class="fas text-xs" :class="it.file_type==='video'?'fa-video text-blue-400':it.file_type==='audio'?'fa-music text-purple-400':it.file_type==='pdf'?'fa-file-pdf text-red-400':'fa-file text-gray-400'"></i>
<span class="text-xs truncate flex-1" :class="{'line-through opacity-40':it.watched}" x-text="it.display_name||it.name"></span>
<span x-show="it.watched" class="text-green-400 text-xs"><i class="fas fa-check-circle"></i></span>
<span class="text-xs text-gray-500" x-text="it.duration?fmt(it.duration):''"></span>
<button @click.stop="toggleWatch(it.hash)" class="opacity-0 group-hover/f:opacity-100 text-xs px-1" :class="it.watched?'text-green-400':'text-gray-500'" :title="it.watched?'Unmark':'Mark watched'"><i class="fas fa-eye"></i></button></div></template>
</div>
</template></div>
<!-- NOTES -->
<div x-show="tab==='notes'" x-cloak class="space-y-3">
<div class="flex mb-3"><select x-model="nF" class="input-field text-sm py-1"><option value="ep">This Episode</option><option value="all">All</option></select>
<select x-model="nS" class="input-field text-sm py-1 ml-2"><option value="newest">Newest</option><option value="oldest">Oldest</option><option value="ts">By Time</option></select></div>
<template x-for="n in sortedNotes" :key="n.id"><div class="bg-gray-800 p-3 rounded">
<div class="flex justify-between mb-1"><a :href="n.timestamp?'/player/'+(hMap[n.file_id]||curHash)+'?t='+Math.floor(n.timestamp):'#'" class="text-xs" :class="n.timestamp?'text-blue-400 hover:text-blue-300':'text-gray-400'" x-text="n.timestamp?fmt(n.timestamp):'General'"></a>
<button @click="delNote(n.id)" class="text-red-400 text-xs"><i class="fas fa-trash"></i></button></div>
<p x-show="nF==='all'" class="text-xs text-gray-500 mb-1 truncate" x-text="fn(n.file_id)"></p>
<p class="text-sm" x-text="n.content"></p></div></template>
<div x-show="sortedNotes.length===0" class="text-center text-gray-500 py-8 text-sm">No notes</div></div>
<!-- BOOKMARKS -->
<div x-show="tab==='bm'" x-cloak class="space-y-2">
<div class="flex mb-3"><select x-model="bF" class="input-field text-sm py-1"><option value="ep">This Episode</option><option value="all">All</option></select>
<select x-model="bS" class="input-field text-sm py-1 ml-2"><option value="ts">By Time</option><option value="newest">Newest</option></select></div>
<template x-for="b in sortedBM" :key="b.id"><div class="flex items-center justify-between p-3 bg-gray-800 rounded hover:bg-gray-700">
<a :href="'/player/'+(hMap[b.file_id]||curHash)+'?t='+Math.floor(b.timestamp)" class="flex-1 text-left min-w-0"><span class="text-sm font-medium" x-text="b.label"></span><span class="text-xs text-gray-400 block" x-text="fmt(b.timestamp)+(bF==='all'?' · '+fn(b.file_id):'')"></span></a>
<button @click="delBM(b.id)" class="text-red-400 text-xs ml-2"><i class="fas fa-trash"></i></button></div></template>
<div x-show="sortedBM.length===0" class="text-center text-gray-500 py-8 text-sm">No bookmarks</div></div>
</div></div></div>
<!-- MODALS -->
<div x-show="showNote" x-cloak class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" @click.self="showNote=false">
<div class="bg-gray-800 rounded-lg p-6 w-full max-w-md"><h2 class="text-xl font-bold mb-4">Add Note</h2>
<form @submit.prevent="addNote()"><label class="flex items-center space-x-2 mb-3"><input type="checkbox" x-model="noteTS"><span class="text-sm">Timestamp: <b x-text="fmt(cur)"></b></span></label>
<textarea x-model="noteC" class="input-field h-32 resize-none mb-4" placeholder="Note..." required></textarea>
<div class="flex justify-end space-x-3"><button type="button" @click="showNote=false" class="btn-secondary">Cancel</button><button type="submit" class="btn-primary">Save</button></div></form></div></div>
<div x-show="showBM" x-cloak class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" @click.self="showBM=false">
<div class="bg-gray-800 rounded-lg p-6 w-full max-w-md"><h2 class="text-xl font-bold mb-4">Add Bookmark</h2>
<p class="mb-4 text-sm">Time: <b x-text="fmt(cur)"></b></p>
<input type="text" x-model="bmL" class="input-field mb-4" placeholder="Label (optional)">
<div class="flex justify-end space-x-3"><button @click="showBM=false" class="btn-secondary">Cancel</button><button @click="addBM()" class="btn-primary">Add</button></div></div></div>
</div>
<script>
function pl(){
  let _tree={{ tree_json|safe }};
  let _wIds={{ watched_file_ids|tojson }};
  let _curH='{{ file.file_hash }}';
  let _allPl=[];
  function collectAll(n){n.children.forEach(c=>collectAll(c));n.files.forEach(f=>_allPl.push({file_hash:f.file_hash}))}
  collectAll(_tree);
  let _curIdx=_allPl.findIndex(f=>f.file_hash===_curH);
  let _hMap={};function buildHMap(n){n.files.forEach(f=>{_hMap[f.id]=f.file_hash});n.children.forEach(c=>buildHMap(c))}buildHMap(_tree);
  let _wHashes=_wIds.map(id=>_hMap[id]).filter(Boolean);
  return {
	playing:false,cur:0,dur:0,vol:1,muted:false,speed:{{ settings.playback_speed }},
	ssOn:{{ 'true' if settings.skip_silence_enabled else 'false' }},ssThresh:{{ settings.skip_silence_db_threshold }},ssSpeed:{{ settings.skip_silence_speed }},
	theaterMode:false,audioCtx:null,analyser:null,
	tab:'pl',showNote:false,showBM:false,noteC:'',noteTS:true,bmL:'',
	curHash:_curH,curIdx:_curIdx,isFirst:_curIdx<=0,isLast:_curIdx>=_allPl.length-1,
	hMap:_hMap,watchedHashes:_wHashes,
	hideW:localStorage.getItem('hideW')==='true',
	plAll:true,folderOpen:{},
	notes:{{ notes|tojson }},bookmarks:{{ bookmarks|tojson }},
	allNotes:{{ all_course_notes|tojson }},allBM:{{ all_course_bookmarks|tojson }},
	nF:'ep',nS:'newest',bF:'ep',bS:'ts',
	pdfDoc:null,pdfPage:1,pdfCount:0,epubR:null,
	allItems:[],
	_tree:_tree,
	saveHideW(){localStorage.setItem('hideW',this.hideW)},
	flatten(n,anc){
	  let items=[];let isR=!n.path;
	  if(!isR){items.push({type:'folder',name:n.name,path:n.path,ancestors:[...anc],depth:anc.length,
		total_duration:n.total_duration,watched_duration:n.watched_duration,file_count:n.file_count})}
	  let fa=isR?[]:[...anc,n.path];
	  for(const c of n.children){items=items.concat(this.flatten(c,fa))}
	  for(const f of n.files){items.push({type:'file',name:f.file_name,hash:f.file_hash,file_type:f.file_type,
		file_id:f.id,watched:this.watchedHashes.includes(f.file_hash),duration:f.duration||0,ancestors:fa,depth:fa.length,display_name:f.display_name})}
	  return items
	},
	toggleFolder(p){this.folderOpen[p]=!this.folderOpen[p]},
	togglePlAll(){this.plAll=!this.plAll;this.folderOpen={}},
	toggleWatch(h){const v=!this.watchedHashes.includes(h);
	  fetch('/api/mark-watched/'+h,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({completed:v})}).then(r=>{
		if(r.ok){if(v&&!this.watchedHashes.includes(h))this.watchedHashes.push(h);else this.watchedHashes=this.watchedHashes.filter(x=>x!==h)}})},
	get visItems(){
	  return this.allItems.filter(item=>{
		if(item.ancestors.some(a=>!(a in this.folderOpen)?!this.plAll:!this.folderOpen[a]))return false;
		if(this.hideW&&item.type==='file'&&item.watched)return false;
		if(this.hideW&&item.type==='folder'){
		  return this.allItems.some(i=>i.type==='file'&&!i.watched&&i.ancestors.includes(item.path)&&
			i.ancestors.every(a=>(a in this.folderOpen)?this.folderOpen[a]:this.plAll))}
		return true})
	},
	get sortedNotes(){let f=this.nF==='ep'?this.notes:this.allNotes;let s=[...f];
	  if(this.nS==='newest')s.sort((a,b)=>new Date(b.created_at)-new Date(a.created_at));
	  else if(this.nS==='oldest')s.sort((a,b)=>new Date(a.created_at)-new Date(b.created_at));
	  else s.sort((a,b)=>(a.timestamp||0)-(b.timestamp||0));return s},
	get sortedBM(){let f=this.bF==='ep'?this.bookmarks:this.allBM;let s=[...f];
	  if(this.bS==='ts')s.sort((a,b)=>a.timestamp-b.timestamp);else s.sort((a,b)=>new Date(b.created_at)-new Date(a.created_at));return s},
	init(){
	  this.allItems=this.flatten(_tree,[]);
	  // Collapse all, then open only ancestors of current file
	  this.plAll=false;
	  const curItem=this.allItems.find(i=>i.type==='file'&&i.hash===this.curHash);
	  if(curItem){curItem.ancestors.forEach(a=>{this.folderOpen[a]=true})}
	  const m=this.$refs.mediaPlayer;
	  if(m){m.currentTime={{ start_time }};m.volume=this.vol;m.playbackRate=this.speed}
	  if(this.ssOn&&m&&m.tagName==='VIDEO')this.initSS();
	  {% if file.file_type=='pdf' %}this.loadPDF();{% endif %}
	  {% if file.file_type=='epub' %}this.loadEPUB();{% endif %}
	  setTimeout(()=>{if(m)m.play().catch(()=>{})},200);
	  // Report duration if not in DB, detect portrait
	  if(m){m.addEventListener('loadedmetadata',()=>{
		if(m.duration&&m.duration!==Infinity&&m.duration>0){
		  fetch('/api/set-duration/'+this.curHash,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({duration:m.duration})}).catch(()=>{})
		}
		if(m.videoHeight&&m.videoWidth){
		  const pc=this.$refs.playerContainer;
		  if(m.videoHeight>m.videoWidth){pc.classList.add('portrait-video')}
		  else{pc.classList.remove('portrait-video')}
		}
	  })}
	  // Scroll to current file in playlist
	  this.$nextTick(()=>{
		const el=document.querySelector('[data-hash="'+this.curHash+'"]');
		if(el){setTimeout(()=>{el.scrollIntoView({behavior:'smooth',block:'center'})},300)}
	  });
	  setInterval(()=>this.saveProg(),10000);
	  // Hotkey polling from AHK
	  setInterval(()=>{fetch('/api/hotkey/poll').then(r=>r.json()).then(d=>{
		(d.actions||[]).forEach(a=>{switch(a){
		  case'play_pause':this.togglePlay();break;case'rewind_5s':this.seek(-5);break;case'forward_5s':this.seek(5);break;
		  case'prev_file':this.goPrev();break;case'next_file':this.goNext();break;
		  case'volume_up':this.chgVol(.1);break;case'volume_down':this.chgVol(-.1);break;
		  case'speed_up':this.chgSpd(.25);break;case'speed_down':this.chgSpd(-.25);break;case'toggle_subtitles':this.toggleSubs();break;
		}})}).catch(()=>{})},300);
	  // Local keyboard
	  document.addEventListener('keydown',e=>{
		if(e.key==='Escape'&&this.theaterMode){this.theaterMode=false;return}
		if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;
		const kc=e.keyCode;if(kc>=96&&kc<=105){e.preventDefault();switch(kc-96){
		  case 5:this.togglePlay();break;case 4:this.seek(-5);break;case 6:this.seek(5);break;
		  case 1:this.goPrev();break;case 3:this.goNext();break;
		  case 8:this.chgVol(.1);break;case 2:this.chgVol(-.1);break;
		  case 9:this.chgSpd(.25);break;case 7:this.chgSpd(-.25);break;case 0:this.toggleSubs();break}}
		if(e.key==='t'||e.key==='T')this.theaterMode=!this.theaterMode;
	  });
	},
	loadPDF(){const lib=window['pdfjs-dist/build/pdf'];lib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
	  lib.getDocument('{{ url_for("player.serve_file",file_hash=file.file_hash) }}').promise.then(d=>{this.pdfDoc=d;this.pdfCount=d.numPages;this.renderPage(1)})},
	renderPage(n){this.pdfDoc.getPage(n).then(p=>{const c=this.$refs.pdfCanvas;const ctx=c.getContext('2d');const vp=p.getViewport({scale:1.5});c.width=vp.width;c.height=vp.height;p.render({canvasContext:ctx,viewport:vp}).promise.then(()=>this.pdfPage=n)})},
	loadEPUB(){try{const b=ePub('{{ url_for("player.serve_file",file_hash=file.file_hash) }}');
	  this.epubR=b.renderTo(this.$refs.epubViewer,{width:'100%',height:'100%',spread:'none',flow:'scrolled-doc'});this.epubR.display()}catch(e){console.error(e)}},
	toggleSS(){this.ssOn=!this.ssOn;const m=this.$refs.mediaPlayer;
	  if(this.ssOn&&m&&m.tagName==='VIDEO')this.initSS();else if(this.audioCtx){try{this.audioCtx.close()}catch(e){};this.audioCtx=null;if(m)m.playbackRate=this.speed}},
	initSS(){const m=this.$refs.mediaPlayer;if(!m||m.tagName!=='VIDEO')return;
	  try{this.audioCtx=new(window.AudioContext||window.webkitAudioContext)();
		const src=this.audioCtx.createMediaElementSource(m);this.analyser=this.audioCtx.createAnalyser();
		src.connect(this.analyser);this.analyser.connect(this.audioCtx.destination);this.analyser.fftSize=2048;
		const buf=new Uint8Array(this.analyser.frequencyBinCount);
		const chk=()=>{if(!this.ssOn||!this.playing){requestAnimationFrame(chk);return}
		  this.analyser.getByteFrequencyData(buf);const avg=buf.reduce((a,b)=>a+b)/buf.length;
		  m.playbackRate=(20*Math.log10(avg/255))<this.ssThresh?this.ssSpeed:this.speed;requestAnimationFrame(chk)};chk()
	  }catch(e){console.error(e)}},
	togglePlay(){const m=this.$refs.mediaPlayer;if(!m)return;
	  if(m.paused)m.play().then(()=>{this.playing=true}).catch(()=>{});else{m.pause();this.playing=false}},
	goPrev(){if(this.curIdx>0)location.href='/player/'+_allPl[this.curIdx-1].file_hash},
	goNext(){if(this.curIdx<_allPl.length-1)location.href='/player/'+_allPl[this.curIdx+1].file_hash},
	seek(s){const m=this.$refs.mediaPlayer;if(m)m.currentTime=Math.max(0,Math.min(m.currentTime+s,this.dur))},
	seekPos(e){const r=this.$refs.progressBar.getBoundingClientRect();const m=this.$refs.mediaPlayer;if(m)m.currentTime=(e.clientX-r.left)/r.width*this.dur},
	updateProgress(){const m=this.$refs.mediaPlayer;this.cur=m.currentTime;this.playing=!m.paused},
	onLoaded(){this.dur=this.$refs.mediaPlayer.duration},
	onEnded(){this.playing=false;
	  if(!this.watchedHashes.includes(this.curHash)){this.watchedHashes.push(this.curHash);
		fetch('/api/mark-watched/'+this.curHash,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({completed:true})})}
	  this.saveProg(true);
	  if(this.curIdx<_allPl.length-1){setTimeout(()=>this.goNext(),1500)}},
	chgVol(d){this.vol=Math.max(0,Math.min(1,this.vol+d));this.updateVol()},
	updateVol(){const m=this.$refs.mediaPlayer;if(m){m.volume=this.vol;this.muted=this.vol===0}},
	toggleMute(){this.muted=!this.muted;if(this.$refs.mediaPlayer)this.$refs.mediaPlayer.muted=this.muted},
	chgSpd(d){this.speed=Math.max(.25,Math.min(4,parseFloat(this.speed)+d));if(this.$refs.mediaPlayer)this.$refs.mediaPlayer.playbackRate=this.speed},
	toggleSubs(){const t=this.$refs.mediaPlayer?.textTracks;if(t?.length)t[0].mode=t[0].mode==='showing'?'hidden':'showing'},
	fs(){const c=this.$refs.playerContainer;if(!document.fullscreenElement)c.requestFullscreen();else document.exitFullscreen()},
	fmt(s){if(!s||isNaN(s))return'0:00';const h=Math.floor(s/3600),m=Math.floor((s%3600)/60),sc=Math.floor(s%60);
	  return h>0?h+':'+String(m).padStart(2,'0')+':'+String(sc).padStart(2,'0'):m+':'+String(sc).padStart(2,'0')},
	fmtH(s){if(!s)return'0m';const h=Math.floor(s/3600),m=Math.floor((s%3600)/60);if(h&&m)return h+'h '+m+'m';if(h)return h+'h';return m+'m'},
	fn(fid){const it=this.allItems.find(i=>i.type==='file'&&i.file_id===fid);return it?it.name:'unknown'},
	saveProg(done){fetch('{{ url_for("player.update_progress",file_hash=file.file_hash) }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_time:this.cur,completed:!!done})}).catch(()=>{})},
	copyTs(){fetch('{{ url_for("player.get_timestamp_link") }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({timestamp:this.cur,file_hash:'{{ file.file_hash }}'})}).then(r=>r.json()).then(d=>{navigator.clipboard.writeText(d.link);alert('Copied!')}).catch(()=>alert('Failed'))},
	addNote(){fetch('{{ url_for("player.manage_notes",file_hash=file.file_hash) }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:this.noteC,timestamp:this.noteTS?this.cur:null})}).then(r=>r.json()).then(d=>{this.notes.unshift(d.note);this.allNotes.unshift(d.note);this.noteC='';this.showNote=false}).catch(()=>alert('Failed'))},
	delNote(id){if(!confirm('Delete?'))return;fetch('/player/notes/'+id,{method:'DELETE'}).then(()=>{this.notes=this.notes.filter(n=>n.id!==id);this.allNotes=this.allNotes.filter(n=>n.id!==id)})},
	addBM(){fetch('{{ url_for("player.manage_bookmarks",file_hash=file.file_hash) }}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({timestamp:this.cur,label:this.bmL||'Bookmark at '+this.fmt(this.cur)})}).then(r=>r.json()).then(d=>{this.bookmarks.push(d.bookmark);this.allBM.push(d.bookmark);this.bmL='';this.showBM=false}).catch(()=>alert('Failed'))},
	delBM(id){if(!confirm('Delete?'))return;fetch('/player/bookmarks/'+id,{method:'DELETE'}).then(()=>{this.bookmarks=this.bookmarks.filter(b=>b.id!==id);this.allBM=this.allBM.filter(b=>b.id!==id)})}
  }
}
</script>
{% endblock %}""",

'settings.html': """{% extends "base.html" %}
{% block title %}Settings{% endblock %}
{% block page_title %}Settings{% endblock %}
{% block content %}
<div x-data="sp()">
<div class="grid grid-cols-12 gap-6">
<div class="col-span-3"><div class="card p-4 space-y-2">
<button @click="sec='player'" :class="sec==='player'?'bg-blue-600':''" class="w-full text-left px-4 py-2 rounded hover:bg-gray-700"><i class="fas fa-play-circle mr-2"></i>Player</button>
<button @click="sec='hotkeys'" :class="sec==='hotkeys'?'bg-blue-600':''" class="w-full text-left px-4 py-2 rounded hover:bg-gray-700"><i class="fas fa-keyboard mr-2"></i>Hotkeys</button>
<button @click="sec='advanced'" :class="sec==='advanced'?'bg-blue-600':''" class="w-full text-left px-4 py-2 rounded hover:bg-gray-700"><i class="fas fa-cog mr-2"></i>Advanced</button>
</div></div>
<div class="col-span-9">
<div x-show="sec==='player'" x-cloak class="space-y-6"><div class="card p-6"><h2 class="text-xl font-bold mb-4">Player Settings</h2>
<form @submit.prevent="save()">
<div class="mb-6"><label class="block text-sm font-medium mb-2">Speed</label><select x-model.number="s.playback_speed" class="input-field"><option value="0.5">0.5x</option><option value="0.75">0.75x</option><option value="1">1x</option><option value="1.25">1.25x</option><option value="1.5">1.5x</option><option value="1.75">1.75x</option><option value="2">2x</option><option value="2.5">2.5x</option><option value="3">3x</option><option value="4">4x</option></select></div>
<div class="mb-6"><label class="flex items-center space-x-2"><input type="checkbox" x-model="s.skip_silence_enabled"><span>Skip Silence</span></label>
<div x-show="s.skip_silence_enabled" x-cloak class="ml-6 mt-3 space-y-3">
<div><label class="block text-sm text-gray-400 mb-1">dB Threshold</label><input type="number" x-model.number="s.skip_silence_db_threshold" class="input-field" min="-60" max="0" step="5"></div>
<div><label class="block text-sm text-gray-400 mb-1">Min Duration</label><input type="number" x-model.number="s.skip_silence_min_duration" class="input-field" min="0.1" max="5" step="0.1"></div>
<div><label class="block text-sm text-gray-400 mb-1">Silence Speed</label><select x-model.number="s.skip_silence_speed" class="input-field"><option value="2">2x</option><option value="3">3x</option><option value="5">5x</option><option value="8">8x</option><option value="10">10x</option></select></div>
</div></div>
<div class="mb-6"><label class="flex items-center space-x-2"><input type="checkbox" x-model="s.subtitle_enabled"><span>Subtitles</span></label></div>
<div class="mb-6"><label class="flex items-center space-x-2"><input type="checkbox" x-model="s.rtl_enabled"><span>RTL</span></label></div>
<div class="mb-6"><label class="flex items-center space-x-2"><input type="checkbox" x-model="s.theater_mode"><span>Theater Mode</span></label></div>
<div class="flex justify-end"><button type="submit" class="btn-primary"><i class="fas fa-save mr-2"></i>Save</button></div></form></div></div>
<div x-show="sec==='hotkeys'" x-cloak class="space-y-6"><div class="card p-6"><h2 class="text-xl font-bold mb-4">Hotkeys (NumPad)</h2>
<p class="text-gray-400 mb-4 text-sm">Run <code class="bg-gray-700 px-2 py-1 rounded">hotkeys.ahk</code> for global control. Works when browser is minimized.</p>
<form @submit.prevent="saveHK()">
<div class="space-y-4"><template x-for="(key,action) in s.hotkeys" :key="action">
<div class="flex items-center justify-between p-3 bg-gray-800 rounded">
<span class="font-medium" x-text="action.replace(/_/g,' ').replace(/\\b\\w/g,l=>l.toUpperCase())"></span>
<select :value="key" @change="s.hotkeys[action]=$event.target.value" class="input-field w-40">
<option value="">None</option><option value="num_0">Num 0</option><option value="num_1">Num 1</option><option value="num_2">Num 2</option>
<option value="num_3">Num 3</option><option value="num_4">Num 4</option><option value="num_5">Num 5</option>
<option value="num_6">Num 6</option><option value="num_7">Num 7</option><option value="num_8">Num 8</option>
<option value="num_9">Num 9</option></select></div></template></div>
<div class="flex justify-end mt-6"><button type="submit" class="btn-primary"><i class="fas fa-save mr-2"></i>Save</button></div></form></div></div>
<div x-show="sec==='advanced'" x-cloak class="space-y-6"><div class="card p-6"><h2 class="text-xl font-bold mb-4">Advanced</h2>
<form @submit.prevent="save()"><div class="mb-6"><label class="block text-sm font-medium mb-2">Timestamp Template</label>
<input type="text" x-model="s.timestamp_template" class="input-field font-mono text-sm">
<p class="text-xs text-gray-500 mt-2">Vars: {HH} {MM} {SS} {url} {timestamp}</p></div>
<div class="flex justify-end"><button type="submit" class="btn-primary"><i class="fas fa-save mr-2"></i>Save</button></div></form></div>
<div class="card p-6 border-red-900"><h2 class="text-xl font-bold mb-4 text-red-400"><i class="fas fa-exclamation-triangle mr-2"></i>Danger Zone</h2>
<div class="flex items-center justify-between p-4 bg-red-900 bg-opacity-20 rounded"><h3 class="text-red-400 font-medium">Reset All Settings</h3>
<button @click="resetAll()" class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded">Reset</button></div></div></div>
</div></div></div>
<script>
function sp(){return{
  sec:'player',s:{{ settings|tojson }},
  save(){fetch("{{ url_for('settings.update') }}",{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(this.s)}).then(r=>alert(r.ok?'Saved!':'Failed')).catch(e=>alert(e.message))},
  saveHK(){fetch("{{ url_for('settings.manage_hotkeys') }}",{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({hotkeys:this.s.hotkeys})}).then(r=>alert(r.ok?'Hotkeys saved! Restart AHK if running.':'Failed')).catch(e=>alert(e.message))},
  resetAll(){if(!confirm('Reset ALL?'))return;fetch("{{ url_for('settings.reset_all') }}",{method:'POST'}).then(r=>{if(r.ok)location.reload()}).catch(e=>alert(e.message))}
}}
</script>
{% endblock %}""",

'creators.html': """{% extends "base.html" %}
{% block title %}Creators{% endblock %}
{% block page_title %}Content Creators{% endblock %}
{% block content %}
<div x-data="creatorsPage()">
<div class="flex justify-between mb-6">
<h2 class="text-2xl font-bold">Content Creators</h2>
<button @click="showModal=true" class="btn-primary"><i class="fas fa-plus mr-2"></i>Add Creator</button>
</div>
{% if creators %}
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
{% for creator in creators %}
<div class="card overflow-hidden group">
<div class="aspect-video bg-gradient-to-br from-purple-600 to-pink-600 relative">
{% if creator.banner %}<img src="{{ creator.banner }}" class="absolute inset-0 w-full h-full object-cover">{% endif %}
<div class="absolute inset-0 flex items-center justify-center">
{% if creator.icon %}<img src="{{ creator.icon }}" class="w-24 h-24 rounded-full border-4 border-white">
{% else %}<i class="fas fa-user text-6xl text-white opacity-50"></i>{% endif %}
</div></div>
<div class="p-4 text-center">
<h3 class="font-semibold text-lg">{{ creator.name }}</h3>
<p class="text-sm text-gray-400 mt-1">{{ creator.courses|length }} courses</p>
<a href="{{ url_for('creators.detail', creator_id=creator.id) }}" class="btn-primary w-full text-center block mt-3">View</a>
</div></div>
{% endfor %}
</div>
{% else %}
<div class="card p-12 text-center"><i class="fas fa-user text-6xl text-gray-600 mb-4"></i>
<h3 class="text-xl font-semibold mb-2">No creators</h3>
<button @click="showModal=true" class="btn-primary"><i class="fas fa-plus mr-2"></i>Add Creator</button></div>
{% endif %}
<div x-show="showModal" x-cloak class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" @click.self="showModal=false">
<div class="bg-gray-800 rounded-lg p-6 w-full max-w-md">
<h2 class="text-2xl font-bold mb-4">Add Creator</h2>
<form @submit.prevent="add()">
<div class="mb-4"><label class="block text-sm font-medium mb-2">Name</label>
<input type="text" x-model="name" class="input-field" required></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Icon</label>
<div class="flex space-x-2">
<input type="text" x-model="icon" class="input-field flex-1" placeholder="Emoji 😀 or URL or FontAwesome">
<input type="file" x-ref="iconFile" @change="uploadIcon()" accept="image/*" class="hidden">
<button type="button" @click="showEmojiPicker=!showEmojiPicker" class="btn-secondary">😀</button>
<button type="button" @click="$refs.iconFile.click()" class="btn-secondary whitespace-nowrap">
<i class="fas fa-upload mr-1"></i>Upload</button>
</div>
<div x-show="showEmojiPicker" x-cloak class="mt-2 p-3 bg-gray-700 rounded-lg grid grid-cols-8 gap-2 max-h-48 overflow-y-auto">
<template x-for="emoji in emojis" :key="emoji">
<button type="button" @click="icon=emoji;showEmojiPicker=false" class="text-2xl hover:bg-gray-600 p-2 rounded" x-text="emoji"></button>
</template>
</div></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Banner</label>
<div class="flex space-x-2">
<input type="text" x-model="banner" class="input-field flex-1" placeholder="URL or upload...">
<input type="file" x-ref="bannerFile" @change="uploadBanner()" accept="image/*" class="hidden">
<button type="button" @click="$refs.bannerFile.click()" class="btn-secondary whitespace-nowrap">
<i class="fas fa-upload mr-1"></i>Upload</button>
</div></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Theme</label>
<select x-model="theme" class="input-field">
<option value="">None (Default)</option>
<option value="dark-blue">Dark Blue</option>
<option value="purple">Purple</option>
<option value="green">Green</option>
<option value="orange">Orange</option>
<option value="red">Red</option>
<option value="pink">Pink</option>
<option value="cyan">Cyan</option>
</select></div>
<div class="flex justify-end space-x-3">
<button type="button" @click="showModal=false" class="btn-secondary">Cancel</button>
<button type="submit" class="btn-primary">Add</button>
</div></form></div></div>
</div>
<script>
function creatorsPage(){return{showModal:false,name:'',icon:'',banner:'',theme:'',showEmojiPicker:false,
emojis:['👤','👨','👩','🧑','👨‍💻','👩‍💻','🧑‍💻','👨‍🎓','👩‍🎓','🧑‍🎓','👨‍🏫','👩‍🏫','🧑‍🏫','🎓','📚','📖','📝','✏️','🖊️','🖋️','✒️','📕','📗','📘','📙','🗂️','📂','📁','💼','🎯','⭐','🌟','✨','💡','🔥','🚀','💻','🖥️','⚡','🎨','🎭','🎪','🎬','🎤','🎧','🎵','🎶','🎸','🎹','🎺','🎻','🏆','🥇','🥈','🥉','🏅','🎖️'],
uploadIcon(){const file=this.$refs.iconFile.files[0];if(!file)return;
const fd=new FormData();fd.append('file',file);
fetch('/upload/image',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
if(d.url)this.icon=d.url;else alert(d.error||'Upload failed')}).catch(e=>alert(e.message))},
uploadBanner(){const file=this.$refs.bannerFile.files[0];if(!file)return;
const fd=new FormData();fd.append('file',file);
fetch('/upload/image',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
if(d.url)this.banner=d.url;else alert(d.error||'Upload failed')}).catch(e=>alert(e.message))},
add(){fetch('/creators/api/create',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({name:this.name,icon:this.icon,banner:this.banner,theme:this.theme})}).then(r=>r.json()).then(d=>{
if(d.error)alert(d.error);else location.reload()}).catch(e=>alert(e.message))}}}
</script>
{% endblock %}""",

'creator_detail.html': """{% extends "base.html" %}
{% block title %}{{ creator.name }}{% endblock %}
{% block page_title %}{{ creator.name }}{% endblock %}
{% block content %}
<div class="mb-6">
<div class="card overflow-hidden">
{% if creator.banner %}
<div class="h-48 bg-cover bg-center" style="background-image:url('{{ creator.banner }}')"></div>
{% else %}
<div class="h-48 bg-gradient-to-r from-purple-600 to-pink-600"></div>
{% endif %}
<div class="p-6 flex items-center space-x-4">
{% if creator.icon %}
<img src="{{ creator.icon }}" class="w-24 h-24 rounded-full border-4 border-gray-700">
{% else %}
<div class="w-24 h-24 rounded-full bg-gray-700 flex items-center justify-center"><i class="fas fa-user text-4xl text-gray-400"></i></div>
{% endif %}
<div><h1 class="text-3xl font-bold">{{ creator.name }}</h1>
<p class="text-gray-400">{{ courses|length }} courses</p></div>
</div></div></div>
{% if continue_watching %}
<div class="mb-8"><h2 class="text-2xl font-bold mb-4">Continue Watching</h2>
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">{% for p in continue_watching %}
<div class="card overflow-hidden">
<div class="aspect-video bg-gray-800 relative flex items-center justify-center">
<i class="fas fa-play-circle text-6xl text-blue-400 opacity-50"></i>
{% if p.file.duration %}<div class="absolute bottom-0 left-0 right-0 h-1 bg-gray-700">
<div class="h-full bg-blue-500" style="width:{{ (p.current_time/p.file.duration*100)|int }}%"></div></div>{% endif %}
</div>
<div class="p-4"><h3 class="font-semibold truncate">{{ p.file.file_name }}</h3>
<p class="text-sm text-gray-400 mt-1"><i class="fas fa-book mr-1"></i>{{ p.file.course.display_name }}</p>
<a href="{{ url_for('player.play',file_hash=p.file.file_hash) }}" class="btn-primary w-full text-center block mt-3"><i class="fas fa-play mr-2"></i>Resume</a>
</div></div>{% endfor %}</div></div>{% endif %}
<div class="mb-6"><h2 class="text-2xl font-bold mb-4">All Courses</h2>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
{% for course in courses %}
<div class="card overflow-hidden">
<div class="aspect-video bg-gradient-to-br from-blue-600 to-purple-600 relative">
{% if course.thumbnail %}<img src="{{ course.thumbnail }}" class="absolute inset-0 w-full h-full object-cover">
{% else %}<div class="absolute inset-0 flex items-center justify-center"><i class="fas fa-book-open text-6xl text-white opacity-50"></i></div>{% endif %}
</div>
<div class="p-4"><h3 class="font-semibold">{{ course.display_name }}</h3>
<p class="text-sm text-gray-400 mt-1">{{ course.total_files }} files</p>
<a href="{{ url_for('courses.detail',course_id=course.id) }}" class="btn-secondary w-full text-center block mt-3">Open</a>
</div></div>{% endfor %}</div></div>
{% endblock %}""",

'categories.html': """{% extends "base.html" %}
{% block title %}Categories{% endblock %}
{% block page_title %}Categories{% endblock %}
{% block content %}
<div x-data="categoriesPage()">
<div class="flex justify-between mb-6">
<h2 class="text-2xl font-bold">Categories</h2>
<button @click="showModal=true" class="btn-primary"><i class="fas fa-plus mr-2"></i>Add Category</button>
</div>
{% if categories %}
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
{% for category in categories %}
<div class="card overflow-hidden group">
<div class="aspect-video bg-gradient-to-br from-blue-600 to-cyan-600 relative">
{% if category.banner %}<img src="{{ category.banner }}" class="absolute inset-0 w-full h-full object-cover">{% endif %}
<div class="absolute inset-0 flex items-center justify-center">
{% if category.icon %}<i class="{{ category.icon }} text-6xl text-white"></i>
{% else %}<i class="fas fa-folder text-6xl text-white opacity-50"></i>{% endif %}
</div></div>
<div class="p-4 text-center">
<h3 class="font-semibold text-lg">{{ category.name }}</h3>
<p class="text-sm text-gray-400 mt-1">{{ category.courses|length }} courses</p>
<a href="{{ url_for('categories.detail', category_id=category.id) }}" class="btn-primary w-full text-center block mt-3">View</a>
</div></div>
{% endfor %}
</div>
{% else %}
<div class="card p-12 text-center"><i class="fas fa-folder text-6xl text-gray-600 mb-4"></i>
<h3 class="text-xl font-semibold mb-2">No categories</h3>
<button @click="showModal=true" class="btn-primary"><i class="fas fa-plus mr-2"></i>Add Category</button></div>
{% endif %}
<div x-show="showModal" x-cloak class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" @click.self="showModal=false">
<div class="bg-gray-800 rounded-lg p-6 w-full max-w-md">
<h2 class="text-2xl font-bold mb-4">Add Category</h2>
<form @submit.prevent="add()">
<div class="mb-4"><label class="block text-sm font-medium mb-2">Name</label>
<input type="text" x-model="name" class="input-field" required></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Icon</label>
<div class="flex space-x-2">
<input type="text" x-model="icon" class="input-field flex-1" placeholder="Emoji 📁 or fas fa-code or URL">
<button type="button" @click="showEmojiPicker=!showEmojiPicker" class="btn-secondary">😀</button>
<input type="file" x-ref="iconFile" @change="uploadIcon()" accept="image/*" class="hidden">
<button type="button" @click="$refs.iconFile.click()" class="btn-secondary whitespace-nowrap">
<i class="fas fa-upload mr-1"></i>Upload</button>
</div>
<div x-show="showEmojiPicker" x-cloak class="mt-2 p-3 bg-gray-700 rounded-lg grid grid-cols-8 gap-2 max-h-48 overflow-y-auto">
<template x-for="emoji in emojis" :key="emoji">
<button type="button" @click="icon=emoji;showEmojiPicker=false" class="text-2xl hover:bg-gray-600 p-2 rounded" x-text="emoji"></button>
</template>
</div></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Banner</label>
<div class="flex space-x-2">
<input type="text" x-model="banner" class="input-field flex-1" placeholder="URL or upload...">
<input type="file" x-ref="bannerFile" @change="uploadBanner()" accept="image/*" class="hidden">
<button type="button" @click="$refs.bannerFile.click()" class="btn-secondary whitespace-nowrap">
<i class="fas fa-upload mr-1"></i>Upload</button>
</div></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Theme</label>
<select x-model="theme" class="input-field">
<option value="">None (Default)</option>
<option value="dark-blue">Dark Blue</option>
<option value="purple">Purple</option>
<option value="green">Green</option>
<option value="orange">Orange</option>
<option value="red">Red</option>
<option value="pink">Pink</option>
<option value="cyan">Cyan</option>
</select></div>
<div class="flex justify-end space-x-3">
<button type="button" @click="showModal=false" class="btn-secondary">Cancel</button>
<button type="submit" class="btn-primary">Add</button>
</div></form></div></div>
</div>
<script>
function categoriesPage(){return{showModal:false,name:'',icon:'',banner:'',theme:'',showEmojiPicker:false,
emojis:['📁','📂','🗂️','📚','📖','📕','📗','📘','📙','💻','🖥️','📱','⌨️','🖱️','💾','💿','📀','🎓','🎯','🚀','⚡','🔥','💡','✨','🌟','⭐','🏆','🥇','🎨','🎭','🎪','🎬','🎤','🎧','🎵','🎶','🎸','🎹','📊','📈','📉','💼','🔧','🔨','⚙️','🛠️','🔬','🔭','🧪','🧬','📡','🎮','🕹️','🎲'],
uploadIcon(){const file=this.$refs.iconFile.files[0];if(!file)return;
const fd=new FormData();fd.append('file',file);
fetch('/upload/image',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
if(d.url)this.icon=d.url;else alert(d.error||'Upload failed')}).catch(e=>alert(e.message))},
uploadBanner(){const file=this.$refs.bannerFile.files[0];if(!file)return;
const fd=new FormData();fd.append('file',file);
fetch('/upload/image',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
if(d.url)this.banner=d.url;else alert(d.error||'Upload failed')}).catch(e=>alert(e.message))},
add(){fetch('/categories/api/create',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({name:this.name,icon:this.icon,banner:this.banner,theme:this.theme})}).then(r=>r.json()).then(d=>{
if(d.error)alert(d.error);else location.reload()}).catch(e=>alert(e.message))}}}
</script>
{% endblock %}""",

'category_detail.html': """{% extends "base.html" %}
{% block title %}{{ category.name }}{% endblock %}
{% block page_title %}{{ category.name }}{% endblock %}
{% block content %}
<div class="mb-6">
<div class="card overflow-hidden">
{% if category.banner %}
<div class="h-48 bg-cover bg-center" style="background-image:url('{{ category.banner }}')"></div>
{% else %}
<div class="h-48 bg-gradient-to-r from-blue-600 to-cyan-600"></div>
{% endif %}
<div class="p-6 flex items-center space-x-4">
<div class="w-24 h-24 rounded-full bg-gray-700 flex items-center justify-center">
{% if category.icon %}<i class="{{ category.icon }} text-4xl text-blue-400"></i>
{% else %}<i class="fas fa-folder text-4xl text-gray-400"></i>{% endif %}
</div>
<div><h1 class="text-3xl font-bold">{{ category.name }}</h1>
<p class="text-gray-400">{{ courses|length }} courses</p></div>
</div></div></div>
{% if continue_watching %}
<div class="mb-8"><h2 class="text-2xl font-bold mb-4">Continue Watching</h2>
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">{% for p in continue_watching %}
<div class="card overflow-hidden">
<div class="aspect-video bg-gray-800 relative flex items-center justify-center">
<i class="fas fa-play-circle text-6xl text-blue-400 opacity-50"></i>
{% if p.file.duration %}<div class="absolute bottom-0 left-0 right-0 h-1 bg-gray-700">
<div class="h-full bg-blue-500" style="width:{{ (p.current_time/p.file.duration*100)|int }}%"></div></div>{% endif %}
</div>
<div class="p-4"><h3 class="font-semibold truncate">{{ p.file.file_name }}</h3>
<p class="text-sm text-gray-400 mt-1"><i class="fas fa-book mr-1"></i>{{ p.file.course.display_name }}</p>
<a href="{{ url_for('player.play',file_hash=p.file.file_hash) }}" class="btn-primary w-full text-center block mt-3"><i class="fas fa-play mr-2"></i>Resume</a>
</div></div>{% endfor %}</div></div>{% endif %}
<div class="mb-6"><h2 class="text-2xl font-bold mb-4">All Courses</h2>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
{% for course in courses %}
<div class="card overflow-hidden">
<div class="aspect-video bg-gradient-to-br from-blue-600 to-purple-600 relative">
{% if course.thumbnail %}<img src="{{ course.thumbnail }}" class="absolute inset-0 w-full h-full object-cover">
{% else %}<div class="absolute inset-0 flex items-center justify-center"><i class="fas fa-book-open text-6xl text-white opacity-50"></i></div>{% endif %}
</div>
<div class="p-4"><h3 class="font-semibold">{{ course.display_name }}</h3>
<p class="text-sm text-gray-400 mt-1">{{ course.total_files }} files</p>
<a href="{{ url_for('courses.detail',course_id=course.id) }}" class="btn-secondary w-full text-center block mt-3">Open</a>
</div></div>{% endfor %}</div></div>
{% endblock %}""",

'tags.html': """{% extends "base.html" %}
{% block title %}Tags{% endblock %}
{% block page_title %}Tags{% endblock %}
{% block content %}
<div x-data="tagsPage()">
<div class="flex justify-between mb-6">
<h2 class="text-2xl font-bold">Tags</h2>
<button @click="showModal=true" class="btn-primary"><i class="fas fa-plus mr-2"></i>Add Tag</button>
</div>
{% if tags %}
<div class="flex flex-wrap gap-3">
{% for tag in tags %}
<a href="{{ url_for('tags.detail', tag_id=tag.id) }}" class="card px-4 py-2 inline-flex items-center space-x-2 hover:bg-blue-600">
{% if tag.icon %}<i class="{{ tag.icon }}"></i>{% else %}<i class="fas fa-tag"></i>{% endif %}
<span>{{ tag.name }}</span>
<span class="text-xs text-gray-400">({{ tag.courses|length }})</span>
</a>
{% endfor %}
</div>
{% else %}
<div class="card p-12 text-center"><i class="fas fa-tag text-6xl text-gray-600 mb-4"></i>
<h3 class="text-xl font-semibold mb-2">No tags</h3>
<button @click="showModal=true" class="btn-primary"><i class="fas fa-plus mr-2"></i>Add Tag</button></div>
{% endif %}
<div x-show="showModal" x-cloak class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" @click.self="showModal=false">
<div class="bg-gray-800 rounded-lg p-6 w-full max-w-md">
<h2 class="text-2xl font-bold mb-4">Add Tag</h2>
<form @submit.prevent="add()">
<div class="mb-4"><label class="block text-sm font-medium mb-2">Name</label>
<input type="text" x-model="name" class="input-field" required></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Icon</label>
<div class="flex space-x-2">
<input type="text" x-model="icon" class="input-field flex-1" placeholder="Emoji 🏷️ or fas fa-star or URL">
<button type="button" @click="showEmojiPicker=!showEmojiPicker" class="btn-secondary">😀</button>
<input type="file" x-ref="iconFile" @change="uploadIcon()" accept="image/*" class="hidden">
<button type="button" @click="$refs.iconFile.click()" class="btn-secondary whitespace-nowrap">
<i class="fas fa-upload mr-1"></i>Upload</button>
</div>
<div x-show="showEmojiPicker" x-cloak class="mt-2 p-3 bg-gray-700 rounded-lg grid grid-cols-8 gap-2 max-h-48 overflow-y-auto">
<template x-for="emoji in emojis" :key="emoji">
<button type="button" @click="icon=emoji;showEmojiPicker=false" class="text-2xl hover:bg-gray-600 p-2 rounded" x-text="emoji"></button>
</template>
</div></div>
<div class="mb-4"><label class="block text-sm font-medium mb-2">Theme</label>
<select x-model="theme" class="input-field">
<option value="">None (Default)</option>
<option value="dark-blue">Dark Blue</option>
<option value="purple">Purple</option>
<option value="green">Green</option>
<option value="orange">Orange</option>
<option value="red">Red</option>
<option value="pink">Pink</option>
<option value="cyan">Cyan</option>
</select></div>
<div class="flex justify-end space-x-3">
<button type="button" @click="showModal=false" class="btn-secondary">Cancel</button>
<button type="submit" class="btn-primary">Add</button>
</div></form></div></div>
</div>
<script>
function tagsPage(){return{showModal:false,name:'',icon:'',theme:'',showEmojiPicker:false,
emojis:['🏷️','📌','📍','🔖','🎯','⭐','✨','💫','🌟','⚡','🔥','💡','💎','🎨','🎭','🎪','🎬','🎤','🎧','🎵','🎶','🎸','🎹','🏆','🥇','🥈','🥉','🏅','🎖️','📚','📖','📕','📗','📘','📙','💻','🖥️','📱','⌨️','🖱️','💾','💿','📀','🎓','🚀','🔧','🔨','⚙️','🛠️'],
uploadIcon(){const file=this.$refs.iconFile.files[0];if(!file)return;
const fd=new FormData();fd.append('file',file);
fetch('/upload/image',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
if(d.url)this.icon=d.url;else alert(d.error||'Upload failed')}).catch(e=>alert(e.message))},
add(){fetch('/tags/api/create',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({name:this.name,icon:this.icon,theme:this.theme})}).then(r=>r.json()).then(d=>{
if(d.error)alert(d.error);else location.reload()}).catch(e=>alert(e.message))}}}
</script>
{% endblock %}""",

'tag_detail.html': """{% extends "base.html" %}
{% block title %}{{ tag.name }}{% endblock %}
{% block page_title %}{{ tag.name }}{% endblock %}
{% block content %}
<div class="mb-6">
<div class="card p-6 flex items-center space-x-4">
<div class="w-16 h-16 rounded-full bg-blue-600 flex items-center justify-center">
{% if tag.icon %}<i class="{{ tag.icon }} text-2xl"></i>
{% else %}<i class="fas fa-tag text-2xl"></i>{% endif %}
</div>
<div><h1 class="text-3xl font-bold">{{ tag.name }}</h1>
<p class="text-gray-400">{{ courses|length }} courses</p></div>
</div></div>
{% if continue_watching %}
<div class="mb-8"><h2 class="text-2xl font-bold mb-4">Continue Watching</h2>
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">{% for p in continue_watching %}
<div class="card overflow-hidden">
<div class="aspect-video bg-gray-800 relative flex items-center justify-center">
<i class="fas fa-play-circle text-6xl text-blue-400 opacity-50"></i>
{% if p.file.duration %}<div class="absolute bottom-0 left-0 right-0 h-1 bg-gray-700">
<div class="h-full bg-blue-500" style="width:{{ (p.current_time/p.file.duration*100)|int }}%"></div></div>{% endif %}
</div>
<div class="p-4"><h3 class="font-semibold truncate">{{ p.file.file_name }}</h3>
<p class="text-sm text-gray-400 mt-1"><i class="fas fa-book mr-1"></i>{{ p.file.course.display_name }}</p>
<a href="{{ url_for('player.play',file_hash=p.file.file_hash) }}" class="btn-primary w-full text-center block mt-3"><i class="fas fa-play mr-2"></i>Resume</a>
</div></div>{% endfor %}</div></div>{% endif %}
<div class="mb-6"><h2 class="text-2xl font-bold mb-4">All Courses</h2>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
{% for course in courses %}
<div class="card overflow-hidden">
<div class="aspect-video bg-gradient-to-br from-blue-600 to-purple-600 relative">
{% if course.thumbnail %}<img src="{{ course.thumbnail }}" class="absolute inset-0 w-full h-full object-cover">
{% else %}<div class="absolute inset-0 flex items-center justify-center"><i class="fas fa-book-open text-6xl text-white opacity-50"></i></div>{% endif %}
</div>
<div class="p-4"><h3 class="font-semibold">{{ course.display_name }}</h3>
<p class="text-sm text-gray-400 mt-1">{{ course.total_files }} files</p>
<a href="{{ url_for('courses.detail',course_id=course.id) }}" class="btn-secondary w-full text-center block mt-3">Open</a>
</div></div>{% endfor %}</div></div>
{% endblock %}""",
}
