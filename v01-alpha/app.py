"""LocalAcademy - Application Factory and Routes"""
import os, json
from flask import (Flask, Blueprint, render_template, request, jsonify,
				   send_file, abort, flash, redirect, url_for, Response)
from datetime import datetime, timezone
from collections import defaultdict
from mimetypes import guess_type
from sqlalchemy import func

from utils import (db, Config, Course, CourseFile, PlaybackProgress, Note, Bookmark,
				   Setting, CourseSetting, Creator, Category, Tag, SETTING_TYPES, THEMES,
				   scan_course_folder, get_folder_structure, tree_to_json,
				   format_duration, format_duration_human, generate_timestamp_link,
				   get_course_theme, start_drive_monitor, start_hotkey_listener, migrate_db)
from html import setup_templates

# ── Blueprints ─────────────────────────────────────────────────────────────────
main_bp = Blueprint('main', __name__)
courses_bp = Blueprint('courses', __name__)
player_bp = Blueprint('player', __name__)
settings_bp = Blueprint('settings', __name__)
creators_bp = Blueprint('creators', __name__)
categories_bp = Blueprint('categories', __name__)
tags_bp = Blueprint('tags', __name__)

# ── Hotkey action queue (AHK → API → browser poll) ────────────────────────────
_hotkey_actions = []

# ── App Factory ────────────────────────────────────────────────────────────────
def create_app():
	app = Flask(__name__)
	app.config.from_object(Config)
	setup_templates(app)
	app.jinja_env.globals['fmt_dur'] = format_duration
	app.jinja_env.globals['fmt_dur_h'] = format_duration_human
	db.init_app(app)
	with app.app_context():
		migrate_db()
		db.create_all()
		Setting.init_defaults()
	app.register_blueprint(main_bp)
	app.register_blueprint(courses_bp, url_prefix='/courses')
	app.register_blueprint(player_bp, url_prefix='/player')
	app.register_blueprint(settings_bp, url_prefix='/settings')
	app.register_blueprint(creators_bp, url_prefix='/creators')
	app.register_blueprint(categories_bp, url_prefix='/categories')
	app.register_blueprint(tags_bp, url_prefix='/tags')
	start_drive_monitor(app)
	start_hotkey_listener(app)
	return app

# ── Main Routes ────────────────────────────────────────────────────────────────
@main_bp.route('/')
def index():
	total = Course.query.count()
	avail = Course.query.filter_by(is_available=True).count()
	# Continue watching: latest unfinished file per course, up to 3 courses
	continue_watching = _get_continue_watching(limit=3)
	recent = Course.query.filter(Course.last_accessed.isnot(None)).order_by(
		Course.last_accessed.desc()).limit(6).all()
	return render_template('index.html', total_courses=total, available_courses=avail,
						   recent_courses=recent, continue_watching=continue_watching)

@main_bp.route('/api/stats')
def api_stats():
	total = Course.query.count()
	avail = Course.query.filter_by(is_available=True).count()
	return jsonify(total_courses=total, available_courses=avail,
				   unavailable_courses=total - avail,
				   total_files=CourseFile.query.count(),
				   total_watched_seconds=int(db.session.query(
					   func.sum(PlaybackProgress.current_time)).scalar() or 0))

@main_bp.route('/search')
def search():
	q = request.args.get('q', '')
	if not q: return jsonify([])
	return jsonify(courses=[c.to_dict() for c in Course.query.filter(
		Course.display_name.contains(q)).limit(10).all()],
		files=[f.to_dict() for f in CourseFile.query.filter(
			CourseFile.file_name.contains(q)).limit(20).all()])

@main_bp.route('/continue-watching')
def continue_watching_page():
	items = _get_continue_watching(limit=None)
	return render_template('continue_watching.html', items=items)

# ── Hotkey API (AHK pushes, browser polls) ────────────────────────────────────
@main_bp.route('/api/hotkey/<action>', methods=['GET', 'POST'])
def push_hotkey(action):
	if request.method == 'GET':
		return jsonify(status='ok', message=f'Send POST to /api/hotkey/{action} to trigger')
	_hotkey_actions.append(action)
	return jsonify(success=True)

@main_bp.route('/api/hotkey/poll')
def poll_hotkeys():
	actions = list(_hotkey_actions)
	_hotkey_actions.clear()
	return jsonify(actions=actions)

# ── Mark Watched API ───────────────────────────────────────────────────────────
@main_bp.route('/api/mark-watched/<string:file_hash>', methods=['POST'])
def mark_watched(file_hash):
	file = CourseFile.query.filter_by(file_hash=file_hash).first_or_404()
	p = PlaybackProgress.query.filter_by(file_id=file.id).first()
	if not p:
		p = PlaybackProgress(course_id=file.course_id, file_id=file.id, current_time=0)
		db.session.add(p)
	data = request.get_json(silent=True) or {}
	p.completed = data.get('completed', True)
	p.last_watched = datetime.now(timezone.utc)
	db.session.commit()
	return jsonify(success=True, completed=p.completed)

@main_bp.route('/api/set-duration/<string:file_hash>', methods=['POST'])
def set_duration(file_hash):
	file = CourseFile.query.filter_by(file_hash=file_hash).first_or_404()
	if file.duration is None:
		data = request.get_json(silent=True) or {}
		dur = data.get('duration')
		if dur and dur > 0:
			file.duration = int(dur)
			db.session.commit()
	return jsonify(success=True)

@main_bp.route('/api/rename/<string:file_hash>', methods=['POST'])
def rename_file(file_hash):
	file = CourseFile.query.filter_by(file_hash=file_hash).first_or_404()
	data = request.get_json(silent=True) or {}
	name = data.get('display_name', '').strip()
	file.display_name = name or None
	db.session.commit()
	return jsonify(success=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
def _get_continue_watching(limit=3):
	"""Get latest unfinished file per course"""
	subq = db.session.query(
		PlaybackProgress.course_id,
		func.max(PlaybackProgress.last_watched).label('max_time')
	).filter(
		PlaybackProgress.completed == False,
		PlaybackProgress.current_time > 0
	).group_by(PlaybackProgress.course_id).order_by(
		func.max(PlaybackProgress.last_watched).desc()
	)
	if limit: subq = subq.limit(limit)
	course_times = subq.all()
	results = []
	for cid, _ in course_times:
		p = PlaybackProgress.query.filter_by(course_id=cid, completed=False
		).filter(PlaybackProgress.current_time > 0
		).order_by(PlaybackProgress.last_watched.desc()).first()
		if p: results.append(p)
	return results

# ── Course Routes ──────────────────────────────────────────────────────────────
@courses_bp.route('/')
def index():
	view = request.args.get('view', 'grid')
	filt = request.args.get('filter', 'all')
	q = Course.query
	if filt == 'available': q = q.filter_by(is_available=True)
	elif filt == 'unavailable': q = q.filter_by(is_available=False)
	return render_template('courses.html', courses=q.order_by(Course.display_name).all(),
						   view_mode=view, filter_type=filt)

@courses_bp.route('/add', methods=['GET', 'POST'])
def add_course():
	if request.method == 'POST':
		data = request.get_json() if request.is_json else request.form
		name, path = data.get('display_name', '').strip(), data.get('root_path', '').strip()
		if not name or not path: return jsonify(error='Name and path required'), 400
		if not os.path.exists(path): return jsonify(error='Path does not exist'), 400
		if Course.query.filter_by(root_path=path).first(): return jsonify(error='Already exists'), 400
		course = Course(display_name=name, root_path=path, is_available=True,
						description=data.get('description', ''))
		if os.name == 'nt' and len(path) > 1 and path[1] == ':':
			course.drive_letter = path[0].upper()
		
		# Add course to session first
		db.session.add(course)
		
		# Handle creators, categories, tags
		creator_ids = data.get('creator_ids', [])
		category_ids = data.get('category_ids', [])
		tag_ids = data.get('tag_ids', [])
		
		if creator_ids:
			course.creators = Creator.query.filter(Creator.id.in_(creator_ids)).all()
		if category_ids:
			course.categories = Category.query.filter(Category.id.in_(category_ids)).all()
		if tag_ids:
			course.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
		
		db.session.commit()
		try: files = scan_course_folder(course)
		except Exception as e: files = []
		if request.is_json: return jsonify(success=True, course_id=course.id, files_found=len(files))
		return redirect(url_for('courses.detail', course_id=course.id))
	return render_template('courses.html', show_add_modal=True)

@courses_bp.route('/<int:course_id>')
def detail(course_id):
	course = Course.query.get_or_404(course_id)
	course.last_accessed = datetime.now(timezone.utc); db.session.commit()
	tree, progress_map, watched_ids = get_folder_structure(course_id)
	theme_name = get_course_theme(course)
	theme_colors = THEMES.get(theme_name, THEMES['default'])
	return render_template('course_detail.html', course=course, tree=tree,
						   progress_map=progress_map, watched_ids=watched_ids,
						   course_creators_json=[c.to_dict() for c in course.creators],
						   course_categories_json=[c.to_dict() for c in course.categories],
						   course_tags_json=[t.to_dict() for t in course.tags],
						   course_description=course.description or '',
						   theme_name=theme_name, theme_colors=theme_colors)

@courses_bp.route('/<int:course_id>/rescan', methods=['POST'])
def rescan_course(course_id):
	course = Course.query.get_or_404(course_id)
	try: files = scan_course_folder(course); return jsonify(success=True, files_count=len(files))
	except Exception as e: return jsonify(error=str(e)), 500

@courses_bp.route('/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
	course = Course.query.get_or_404(course_id)
	name = course.display_name; db.session.delete(course); db.session.commit()
	flash(f'Course "{name}" deleted', 'success')
	return jsonify(success=True) if request.is_json else redirect(url_for('courses.index'))

@courses_bp.route('/<int:course_id>/thumbnail', methods=['POST'])
def update_thumbnail(course_id):
	course = Course.query.get_or_404(course_id)
	data = request.get_json() if request.is_json else request.form
	course.thumbnail = data.get('thumbnail', '').strip() or None; db.session.commit()
	return jsonify(success=True) if request.is_json else redirect(url_for('courses.detail', course_id=course_id))

@courses_bp.route('/<int:course_id>/metadata', methods=['POST'])
def update_metadata(course_id):
	course = Course.query.get_or_404(course_id)
	data = request.get_json()
	
	if 'description' in data:
		course.description = data['description']
	if 'theme' in data:
		course.theme = data['theme']
	if 'creator_ids' in data:
		course.creators = Creator.query.filter(Creator.id.in_(data['creator_ids'])).all()
	if 'category_ids' in data:
		# Categories come in order, preserve it
		category_ids = data['category_ids']
		categories = Category.query.filter(Category.id.in_(category_ids)).all()
		# Sort by the order in category_ids
		category_map = {c.id: c for c in categories}
		course.categories = [category_map[cid] for cid in category_ids if cid in category_map]
	if 'tag_ids' in data:
		course.tags = Tag.query.filter(Tag.id.in_(data['tag_ids'])).all()
	
	db.session.commit()
	return jsonify(success=True)

@courses_bp.route('/<int:course_id>/files')
def get_files(course_id):
	Course.query.get_or_404(course_id)
	return jsonify(files=[f.to_dict() for f in CourseFile.query.filter_by(
		course_id=course_id).order_by(CourseFile.parent_folder, CourseFile.order_index).all()])

@courses_bp.route('/available')
def available():
	return render_template('courses.html',
		courses=Course.query.filter_by(is_available=True).order_by(Course.display_name).all(),
		filter_type='available')

@courses_bp.route('/unavailable')
def unavailable():
	return render_template('courses.html',
		courses=Course.query.filter_by(is_available=False).order_by(Course.display_name).all(),
		filter_type='unavailable')

# ── Player Routes ──────────────────────────────────────────────────────────────
@player_bp.route('/<string:file_hash>')
def play(file_hash):
	file = CourseFile.query.filter_by(file_hash=file_hash).first_or_404()
	course = file.course
	if not course.is_available: abort(404, "Course unavailable")
	progress = PlaybackProgress.query.filter_by(file_id=file.id).first()
	if not progress:
		progress = PlaybackProgress(course_id=course.id, file_id=file.id, current_time=0.0)
		db.session.add(progress); db.session.commit()
	# Settings
	gset = {k: Setting.get(k, getattr(Config, f'DEFAULT_{k.upper()}', v))
			for k, v in {'playback_speed': 1.0, 'skip_silence_enabled': False,
			'skip_silence_db_threshold': -40, 'skip_silence_min_duration': 0.3,
			'skip_silence_speed': 5.0, 'subtitle_enabled': True, 'rtl_enabled': False,
			'theater_mode': False}.items()}
	cs = CourseSetting.query.filter_by(course_id=course.id).first()
	if cs:
		for k in gset:
			v = getattr(cs, k, None)
			if v is not None: gset[k] = v
	notes = [n.to_dict() for n in Note.query.filter_by(file_id=file.id).order_by(Note.created_at.desc()).all()]
	bmarks = [b.to_dict() for b in Bookmark.query.filter_by(file_id=file.id).order_by(Bookmark.timestamp).all()]
	all_notes = [n.to_dict() for n in Note.query.join(CourseFile).filter(
		CourseFile.course_id == course.id).order_by(Note.created_at.desc()).all()]
	all_bmarks = [b.to_dict() for b in Bookmark.query.join(CourseFile).filter(
		CourseFile.course_id == course.id).order_by(Bookmark.timestamp).all()]
	tree, _, watched = get_folder_structure(course.id)
	tree_json = json.dumps(tree_to_json(tree))
	watched = list(watched)
	subs = []
	if file.file_type == 'video':
		base_name = os.path.splitext(file.file_name)[0]
		subs = CourseFile.query.filter_by(course_id=course.id, parent_folder=file.parent_folder,
			file_type='subtitle').filter(CourseFile.file_name.startswith(base_name)).all()
	start = request.args.get('t', progress.current_time, type=float)
	theme_name = get_course_theme(course)
	theme_colors = THEMES.get(theme_name, THEMES['default'])
	return render_template('player.html', file=file, course=course, progress=progress,
		settings=gset, notes=notes, bookmarks=bmarks, all_course_notes=all_notes,
		all_course_bookmarks=all_bmarks, tree_json=tree_json,
		subtitle_files=subs, start_time=start, watched_file_ids=watched,
		theme_name=theme_name, theme_colors=theme_colors)

@player_bp.route('/serve/<string:file_hash>')
def serve_file(file_hash):
	file = CourseFile.query.filter_by(file_hash=file_hash).first_or_404()
	if not file.course.is_available or not os.path.exists(file.file_path): abort(404)
	mime, _ = guess_type(file.file_path)
	rng = request.headers.get('Range')
	if rng: return _send_range(file.file_path, rng, mime)
	if file.file_type == 'pdf':
		resp = send_file(file.file_path, mimetype='application/pdf')
		resp.headers['Content-Disposition'] = 'inline'
		return resp
	return send_file(file.file_path, mimetype=mime)

@player_bp.route('/thumbnail/<string:file_hash>')
def serve_thumbnail(file_hash):
	"""Serve video thumbnail"""
	file = CourseFile.query.filter_by(file_hash=file_hash).first_or_404()
	if file.thumbnail and os.path.exists(file.thumbnail):
		return send_file(file.thumbnail, mimetype='image/jpeg')
	abort(404)

@main_bp.route('/thumbnails/<path:filename>')
def serve_thumbnail_file(filename):
	"""Serve thumbnail files from instance/thumbnails"""
	thumb_dir = os.path.join('instance', 'thumbnails')
	return send_file(os.path.join(thumb_dir, filename), mimetype='image/jpeg')

@main_bp.route('/upload/image', methods=['POST'])
def upload_image():
	"""Upload image for icons/banners"""
	if 'file' not in request.files:
		return jsonify(error='No file'), 400
	
	file = request.files['file']
	if file.filename == '':
		return jsonify(error='No file selected'), 400
	
	# Check file extension
	allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
	ext = os.path.splitext(file.filename)[1].lower()
	if ext not in allowed_extensions:
		return jsonify(error='Invalid file type'), 400
	
	# Create uploads directory
	upload_dir = os.path.join('instance', 'uploads')
	os.makedirs(upload_dir, exist_ok=True)
	
	# Generate unique filename
	import hashlib, time
	unique_name = hashlib.md5(f'{file.filename}{time.time()}'.encode()).hexdigest()[:16]
	filename = f'{unique_name}{ext}'
	filepath = os.path.join(upload_dir, filename)
	
	# Save file
	file.save(filepath)
	
	# Return web path
	return jsonify(url=f'/uploads/{filename}')

@main_bp.route('/uploads/<path:filename>')
def serve_upload(filename):
	"""Serve uploaded files"""
	upload_dir = os.path.join('instance', 'uploads')
	return send_file(os.path.join(upload_dir, filename))

def _send_range(path, range_header, mime=None):
	size = os.path.getsize(path)
	parts = range_header.replace('bytes=', '').split('-')
	start = int(parts[0]) if parts[0] else 0
	end = int(parts[1]) if parts[1] else size - 1
	length = end - start + 1
	with open(path, 'rb') as f: f.seek(start); data = f.read(length)
	resp = Response(data, 206, mimetype=mime or 'application/octet-stream', direct_passthrough=True)
	resp.headers.add('Content-Range', f'bytes {start}-{end}/{size}')
	resp.headers.add('Accept-Ranges', 'bytes'); resp.headers.add('Content-Length', str(length))
	return resp

@player_bp.route('/progress/<string:file_hash>', methods=['POST'])
def update_progress(file_hash):
	file = CourseFile.query.filter_by(file_hash=file_hash).first_or_404()
	data = request.get_json()
	p = PlaybackProgress.query.filter_by(file_id=file.id).first()
	if not p: p = PlaybackProgress(course_id=file.course_id, file_id=file.id); db.session.add(p)
	p.current_time = data.get('current_time', 0); p.completed = data.get('completed', False)
	p.last_watched = datetime.now(timezone.utc); db.session.commit()
	return jsonify(success=True)

@player_bp.route('/notes/<string:file_hash>', methods=['GET', 'POST'])
def manage_notes(file_hash):
	file = CourseFile.query.filter_by(file_hash=file_hash).first_or_404()
	if request.method == 'POST':
		data = request.get_json(); content = data.get('content', '').strip()
		if not content: return jsonify(error='Content required'), 400
		note = Note(file_id=file.id, content=content, timestamp=data.get('timestamp'))
		db.session.add(note); db.session.commit()
		return jsonify(success=True, note=note.to_dict())
	return jsonify(notes=[n.to_dict() for n in Note.query.filter_by(file_id=file.id).order_by(Note.created_at.desc()).all()])

@player_bp.route('/notes/<int:note_id>', methods=['PUT', 'DELETE'])
def edit_note(note_id):
	note = Note.query.get_or_404(note_id)
	if request.method == 'PUT':
		note.content = request.get_json().get('content', note.content)
		note.updated_at = datetime.now(timezone.utc); db.session.commit()
		return jsonify(success=True, note=note.to_dict())
	db.session.delete(note); db.session.commit(); return jsonify(success=True)

@player_bp.route('/bookmarks/<string:file_hash>', methods=['GET', 'POST'])
def manage_bookmarks(file_hash):
	file = CourseFile.query.filter_by(file_hash=file_hash).first_or_404()
	if request.method == 'POST':
		data = request.get_json(); ts = data.get('timestamp')
		if ts is None: return jsonify(error='Timestamp required'), 400
		bm = Bookmark(file_id=file.id, timestamp=ts, label=data.get('label', '').strip() or f'Bookmark at {int(ts)}s')
		db.session.add(bm); db.session.commit()
		return jsonify(success=True, bookmark=bm.to_dict())
	return jsonify(bookmarks=[b.to_dict() for b in Bookmark.query.filter_by(file_id=file.id).order_by(Bookmark.timestamp).all()])

@player_bp.route('/bookmarks/<int:bookmark_id>', methods=['DELETE'])
def delete_bookmark(bookmark_id):
	db.session.delete(Bookmark.query.get_or_404(bookmark_id)); db.session.commit()
	return jsonify(success=True)

@player_bp.route('/timestamp-link', methods=['POST'])
def get_timestamp_link():
	data = request.get_json()
	return jsonify(link=generate_timestamp_link(data.get('timestamp', 0), data.get('file_hash')))

# ── Settings Routes ────────────────────────────────────────────────────────────
@settings_bp.route('/')
def index():
	settings = {k: Setting.get(k, getattr(Config, f'DEFAULT_{k.upper()}', d))
				for k, d in {'playback_speed': 1.0, 'skip_silence_enabled': False,
				'skip_silence_db_threshold': -40, 'skip_silence_min_duration': 0.3,
				'subtitle_enabled': True, 'rtl_enabled': False, 'theater_mode': False,
				'timestamp_template': '[{HH}:{MM}:{SS}]({url})'}.items()}
	settings['hotkeys'] = Setting.get('hotkeys', Config.DEFAULT_HOTKEYS)
	settings['skip_silence_speed'] = Setting.get('skip_silence_speed', 5.0)
	return render_template('settings.html', settings=settings)

@settings_bp.route('/update', methods=['POST'])
def update():
	data = request.get_json() if request.is_json else request.form
	for key, type_fn in SETTING_TYPES.items():
		if key in data:
			val = bool(data.get(key)) if type_fn == bool else type_fn(data[key])
			Setting.set(key, val)
	if 'hotkeys' in data: Setting.set('hotkeys', data['hotkeys'])
	flash('Settings updated', 'success')
	return jsonify(success=True) if request.is_json else redirect(url_for('settings.index'))

@settings_bp.route('/course/<int:course_id>', methods=['GET', 'POST'])
def course_settings(course_id):
	course = Course.query.get_or_404(course_id)
	if request.method == 'POST':
		data = request.get_json() if request.is_json else request.form
		cs = CourseSetting.query.filter_by(course_id=course_id).first()
		if not cs: cs = CourseSetting(course_id=course_id); db.session.add(cs)
		for key in SETTING_TYPES:
			if key in data:
				val = data[key]
				if val is not None and val != '':
					setattr(cs, key, bool(val) if SETTING_TYPES[key] == bool else SETTING_TYPES[key](val))
		db.session.commit()
		if request.is_json: return jsonify(success=True)
		flash('Course settings updated', 'success')
		return redirect(url_for('courses.detail', course_id=course_id))
	if request.is_json or request.headers.get('Accept') == 'application/json':
		cs = CourseSetting.query.filter_by(course_id=course_id).first()
		return jsonify(cs.to_dict()) if cs else jsonify({})
	return render_template('course_settings.html', course=course)

@settings_bp.route('/course/<int:course_id>/reset', methods=['POST'])
def reset_course_settings(course_id):
	cs = CourseSetting.query.filter_by(course_id=course_id).first()
	if cs: db.session.delete(cs); db.session.commit()
	return jsonify(success=True)

@settings_bp.route('/hotkeys', methods=['GET', 'POST'])
def manage_hotkeys():
	if request.method == 'POST':
		Setting.set('hotkeys', request.get_json().get('hotkeys', {}))
		return jsonify(success=True)
	return jsonify(hotkeys=Setting.get('hotkeys', Config.DEFAULT_HOTKEYS))

@settings_bp.route('/reset', methods=['POST'])
def reset_all():
	Setting.query.delete(); db.session.commit(); Setting.init_defaults()
	flash('Settings reset', 'success')
	return jsonify(success=True) if request.is_json else redirect(url_for('settings.index'))

# ── Creator Routes ─────────────────────────────────────────────────────────────
@creators_bp.route('/')
def index():
	creators = Creator.query.order_by(Creator.name).all()
	return render_template('creators.html', creators=creators)

@creators_bp.route('/<int:creator_id>')
def detail(creator_id):
	creator = Creator.query.get_or_404(creator_id)
	courses = creator.courses
	continue_watching = _get_continue_watching_for_courses([c.id for c in courses])
	return render_template('creator_detail.html', creator=creator, courses=courses,
						   continue_watching=continue_watching)

@creators_bp.route('/api/all')
def api_all():
	return jsonify([c.to_dict() for c in Creator.query.order_by(Creator.name).all()])

@creators_bp.route('/api/create', methods=['POST'])
def api_create():
	data = request.get_json()
	name = data.get('name', '').strip()
	if not name: return jsonify(error='Name required'), 400
	if Creator.query.filter_by(name=name).first():
		return jsonify(error='Already exists'), 400
	creator = Creator(name=name, icon=data.get('icon'), banner=data.get('banner'),
					  theme=data.get('theme'))
	db.session.add(creator); db.session.commit()
	return jsonify(creator.to_dict())

@creators_bp.route('/api/<int:creator_id>', methods=['PUT', 'DELETE'])
def api_manage(creator_id):
	creator = Creator.query.get_or_404(creator_id)
	if request.method == 'DELETE':
		db.session.delete(creator); db.session.commit()
		return jsonify(success=True)
	data = request.get_json()
	if 'name' in data: creator.name = data['name']
	if 'icon' in data: creator.icon = data['icon']
	if 'banner' in data: creator.banner = data['banner']
	if 'theme' in data: creator.theme = data['theme']
	db.session.commit()
	return jsonify(creator.to_dict())

# ── Category Routes ────────────────────────────────────────────────────────────
@categories_bp.route('/')
def index():
	categories = Category.query.order_by(Category.name).all()
	return render_template('categories.html', categories=categories)

@categories_bp.route('/<int:category_id>')
def detail(category_id):
	category = Category.query.get_or_404(category_id)
	courses = category.courses
	continue_watching = _get_continue_watching_for_courses([c.id for c in courses])
	return render_template('category_detail.html', category=category, courses=courses,
						   continue_watching=continue_watching)

@categories_bp.route('/api/all')
def api_all():
	return jsonify([c.to_dict() for c in Category.query.order_by(Category.name).all()])

@categories_bp.route('/api/create', methods=['POST'])
def api_create():
	data = request.get_json()
	name = data.get('name', '').strip()
	if not name: return jsonify(error='Name required'), 400
	if Category.query.filter_by(name=name).first():
		return jsonify(error='Already exists'), 400
	category = Category(name=name, icon=data.get('icon'), banner=data.get('banner'),
						theme=data.get('theme'))
	db.session.add(category); db.session.commit()
	return jsonify(category.to_dict())

@categories_bp.route('/api/<int:category_id>', methods=['PUT', 'DELETE'])
def api_manage(category_id):
	category = Category.query.get_or_404(category_id)
	if request.method == 'DELETE':
		db.session.delete(category); db.session.commit()
		return jsonify(success=True)
	data = request.get_json()
	if 'name' in data: category.name = data['name']
	if 'icon' in data: category.icon = data['icon']
	if 'banner' in data: category.banner = data['banner']
	if 'theme' in data: category.theme = data['theme']
	db.session.commit()
	return jsonify(category.to_dict())

# ── Tag Routes ─────────────────────────────────────────────────────────────────
@tags_bp.route('/')
def index():
	tags = Tag.query.order_by(Tag.name).all()
	return render_template('tags.html', tags=tags)

@tags_bp.route('/<int:tag_id>')
def detail(tag_id):
	tag = Tag.query.get_or_404(tag_id)
	courses = tag.courses
	continue_watching = _get_continue_watching_for_courses([c.id for c in courses])
	return render_template('tag_detail.html', tag=tag, courses=courses,
						   continue_watching=continue_watching)

@tags_bp.route('/api/all')
def api_all():
	return jsonify([t.to_dict() for t in Tag.query.order_by(Tag.name).all()])

@tags_bp.route('/api/create', methods=['POST'])
def api_create():
	data = request.get_json()
	name = data.get('name', '').strip()
	if not name: return jsonify(error='Name required'), 400
	if Tag.query.filter_by(name=name).first():
		return jsonify(error='Already exists'), 400
	tag = Tag(name=name, icon=data.get('icon'), banner=data.get('banner'),
			  theme=data.get('theme'))
	db.session.add(tag); db.session.commit()
	return jsonify(tag.to_dict())

@tags_bp.route('/api/<int:tag_id>', methods=['PUT', 'DELETE'])
def api_manage(tag_id):
	tag = Tag.query.get_or_404(tag_id)
	if request.method == 'DELETE':
		db.session.delete(tag); db.session.commit()
		return jsonify(success=True)
	data = request.get_json()
	if 'name' in data: tag.name = data['name']
	if 'icon' in data: tag.icon = data['icon']
	if 'banner' in data: tag.banner = data['banner']
	if 'theme' in data: tag.theme = data['theme']
	db.session.commit()
	return jsonify(tag.to_dict())

# ── Helper for continue watching by courses ────────────────────────────────────
def _get_continue_watching_for_courses(course_ids, limit=None):
	"""Get continue watching for specific courses"""
	if not course_ids: return []
	subq = db.session.query(
		PlaybackProgress.course_id,
		func.max(PlaybackProgress.last_watched).label('max_time')
	).filter(
		PlaybackProgress.course_id.in_(course_ids),
		PlaybackProgress.completed == False,
		PlaybackProgress.current_time > 0
	).group_by(PlaybackProgress.course_id).order_by(
		func.max(PlaybackProgress.last_watched).desc()
	)
	if limit: subq = subq.limit(limit)
	course_times = subq.all()
	results = []
	for cid, _ in course_times:
		p = PlaybackProgress.query.filter_by(course_id=cid, completed=False
		).filter(PlaybackProgress.current_time > 0
		).order_by(PlaybackProgress.last_watched.desc()).first()
		if p: results.append(p)
	return results

# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
	app = create_app()
	app.run(debug=True, host='0.0.0.0', port=5000)
