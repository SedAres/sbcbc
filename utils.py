"""LocalAcademy - Config, Models, Utilities, and Background Services"""
import os, hashlib, threading, time, json, re
from datetime import datetime, timezone
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ── Themes ─────────────────────────────────────────────────────────────────────
THEMES = {
	'default': {'primary': '#3b82f6', 'secondary': '#8b5cf6', 'accent': '#06b6d4', 'bg': '#0f1419'},
	'dark-blue': {'primary': '#2563eb', 'secondary': '#1e40af', 'accent': '#3b82f6', 'bg': '#0c1221'},
	'purple': {'primary': '#9333ea', 'secondary': '#7c3aed', 'accent': '#c084fc', 'bg': '#1a0a2e'},
	'green': {'primary': '#10b981', 'secondary': '#059669', 'accent': '#34d399', 'bg': '#064e3b'},
	'orange': {'primary': '#f59e0b', 'secondary': '#d97706', 'accent': '#fbbf24', 'bg': '#78350f'},
	'red': {'primary': '#ef4444', 'secondary': '#dc2626', 'accent': '#f87171', 'bg': '#7f1d1d'},
	'pink': {'primary': '#ec4899', 'secondary': '#db2777', 'accent': '#f472b6', 'bg': '#831843'},
	'cyan': {'primary': '#06b6d4', 'secondary': '#0891b2', 'accent': '#22d3ee', 'bg': '#164e63'},
}

# ── Configuration ──────────────────────────────────────────────────────────────
class Config:
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///localacademy.db'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	MAX_CONTENT_LENGTH = 16 * 1024 * 1024

	VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
	AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}
	PDF_EXTENSIONS = {'.pdf'}
	EPUB_EXTENSIONS = {'.epub'}
	IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
	SUBTITLE_EXTENSIONS = {'.srt', '.vtt', '.ass', '.ssa', '.sub'}

	DEFAULT_PLAYBACK_SPEED = 1.0
	DEFAULT_SKIP_SILENCE_ENABLED = False
	DEFAULT_SKIP_SILENCE_DB_THRESHOLD = -40
	DEFAULT_SKIP_SILENCE_MIN_DURATION = 0.3
	DEFAULT_SKIP_SILENCE_SPEED = 5.0
	DEFAULT_SUBTITLE_ENABLED = True
	DEFAULT_RTL_ENABLED = False
	DEFAULT_AUDIO_DEVICE = 'default'
	DEFAULT_HOTKEYS = {
		'play_pause': 'num_5', 'rewind_5s': 'num_4', 'forward_5s': 'num_6',
		'prev_file': 'num_1', 'next_file': 'num_3',
		'volume_up': 'num_8', 'volume_down': 'num_2',
		'speed_up': 'num_9', 'speed_down': 'num_7',
		'toggle_subtitles': 'num_0',
	}

# ── Association Tables ────────────────────────────────────────────────────────
course_creators = db.Table('course_creators',
	db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
	db.Column('creator_id', db.Integer, db.ForeignKey('creators.id'), primary_key=True)
)

course_categories = db.Table('course_categories',
	db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
	db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True),
	db.Column('order_index', db.Integer, default=0)
)

course_tags = db.Table('course_tags',
	db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
	db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

# ── Models ─────────────────────────────────────────────────────────────────────
class Creator(db.Model):
	__tablename__ = 'creators'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255), nullable=False, unique=True)
	icon = db.Column(db.String(512))
	banner = db.Column(db.String(512))
	theme = db.Column(db.String(50))
	created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
	courses = db.relationship('Course', secondary=course_creators, back_populates='creators')
	
	def to_dict(self):
		return {'id': self.id, 'name': self.name, 'icon': self.icon, 
				'banner': self.banner, 'theme': self.theme}

class Category(db.Model):
	__tablename__ = 'categories'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255), nullable=False, unique=True)
	icon = db.Column(db.String(512))
	banner = db.Column(db.String(512))
	theme = db.Column(db.String(50))
	created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
	courses = db.relationship('Course', secondary=course_categories, back_populates='categories')
	
	def to_dict(self):
		return {'id': self.id, 'name': self.name, 'icon': self.icon,
				'banner': self.banner, 'theme': self.theme}

class Tag(db.Model):
	__tablename__ = 'tags'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255), nullable=False, unique=True)
	icon = db.Column(db.String(512))
	banner = db.Column(db.String(512))
	theme = db.Column(db.String(50))
	created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
	courses = db.relationship('Course', secondary=course_tags, back_populates='tags')
	
	def to_dict(self):
		return {'id': self.id, 'name': self.name, 'icon': self.icon,
				'banner': self.banner, 'theme': self.theme}

class Course(db.Model):
	__tablename__ = 'courses'
	id = db.Column(db.Integer, primary_key=True)
	display_name = db.Column(db.String(255), nullable=False)
	root_path = db.Column(db.String(512), nullable=False, unique=True)
	is_available = db.Column(db.Boolean, default=False)
	drive_letter = db.Column(db.String(10))
	thumbnail = db.Column(db.String(512))
	description = db.Column(db.Text)
	theme = db.Column(db.String(50))
	total_files = db.Column(db.Integer, default=0)
	total_duration = db.Column(db.Integer, default=0)
	created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
	last_accessed = db.Column(db.DateTime)
	files = db.relationship('CourseFile', back_populates='course', cascade='all, delete-orphan')
	progress = db.relationship('PlaybackProgress', back_populates='course', cascade='all, delete-orphan')
	settings = db.relationship('CourseSetting', back_populates='course', cascade='all, delete-orphan', uselist=False)
	creators = db.relationship('Creator', secondary=course_creators, back_populates='courses')
	categories = db.relationship('Category', secondary=course_categories, back_populates='courses')
	tags = db.relationship('Tag', secondary=course_tags, back_populates='courses')

	def to_dict(self):
		return {k: (v.isoformat() if isinstance(v, datetime) else v)
				for k, v in {'id': self.id, 'display_name': self.display_name,
				'root_path': self.root_path, 'is_available': self.is_available,
				'thumbnail': self.thumbnail, 'description': self.description,
				'theme': self.theme, 'total_files': self.total_files,
				'total_duration': self.total_duration, 'created_at': self.created_at,
				'last_accessed': self.last_accessed,
				'creators': [c.to_dict() for c in self.creators],
				'categories': [c.to_dict() for c in self.categories],
				'tags': [t.to_dict() for t in self.tags]}.items() if v is not None or k in ('id','display_name','root_path','is_available','total_files')}

class CourseFile(db.Model):
	__tablename__ = 'course_files'
	id = db.Column(db.Integer, primary_key=True)
	file_hash = db.Column(db.String(16), unique=True, nullable=False)
	course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
	file_path = db.Column(db.String(512), nullable=False)
	relative_path = db.Column(db.String(512), nullable=False)
	file_name = db.Column(db.String(255), nullable=False)
	display_name = db.Column(db.String(255))
	file_type = db.Column(db.String(20), nullable=False)
	file_extension = db.Column(db.String(10), nullable=False)
	file_size = db.Column(db.BigInteger, default=0)
	duration = db.Column(db.Integer)
	thumbnail = db.Column(db.String(512))
	video_quality = db.Column(db.String(20))
	parent_folder = db.Column(db.String(512))
	order_index = db.Column(db.Integer, default=0)
	created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
	course = db.relationship('Course', back_populates='files')
	progress = db.relationship('PlaybackProgress', back_populates='file', cascade='all, delete-orphan')
	notes = db.relationship('Note', back_populates='file', cascade='all, delete-orphan')
	bookmarks = db.relationship('Bookmark', back_populates='file', cascade='all, delete-orphan')

	def to_dict(self):
		return {'id': self.id, 'file_hash': self.file_hash, 'course_id': self.course_id,
				'file_path': self.file_path, 'relative_path': self.relative_path,
				'file_name': self.file_name, 'display_name': self.display_name or self.file_name,
				'file_type': self.file_type, 'file_extension': self.file_extension,
				'file_size': self.file_size, 'duration': self.duration, 'thumbnail': self.thumbnail,
				'video_quality': self.video_quality, 'parent_folder': self.parent_folder, 
				'order_index': self.order_index}

class PlaybackProgress(db.Model):
	__tablename__ = 'playback_progress'
	id = db.Column(db.Integer, primary_key=True)
	course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
	file_id = db.Column(db.Integer, db.ForeignKey('course_files.id'), nullable=False)
	current_time = db.Column(db.Float, default=0.0)
	completed = db.Column(db.Boolean, default=False)
	last_watched = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
	course = db.relationship('Course', back_populates='progress')
	file = db.relationship('CourseFile', back_populates='progress')

	def to_dict(self):
		return {'id': self.id, 'file_id': self.file_id, 'current_time': self.current_time,
				'completed': self.completed,
				'last_watched': self.last_watched.isoformat() if self.last_watched else None}

class Note(db.Model):
	__tablename__ = 'notes'
	id = db.Column(db.Integer, primary_key=True)
	file_id = db.Column(db.Integer, db.ForeignKey('course_files.id'), nullable=False)
	timestamp = db.Column(db.Float)
	content = db.Column(db.Text, nullable=False)
	created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
	updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
	file = db.relationship('CourseFile', back_populates='notes')

	def to_dict(self):
		return {'id': self.id, 'file_id': self.file_id, 'timestamp': self.timestamp,
				'content': self.content,
				'created_at': self.created_at.isoformat() if self.created_at else None,
				'updated_at': self.updated_at.isoformat() if self.updated_at else None}

class Bookmark(db.Model):
	__tablename__ = 'bookmarks'
	id = db.Column(db.Integer, primary_key=True)
	file_id = db.Column(db.Integer, db.ForeignKey('course_files.id'), nullable=False)
	timestamp = db.Column(db.Float, nullable=False)
	label = db.Column(db.String(255))
	created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
	file = db.relationship('CourseFile', back_populates='bookmarks')

	def to_dict(self):
		return {'id': self.id, 'file_id': self.file_id, 'timestamp': self.timestamp,
				'label': self.label,
				'created_at': self.created_at.isoformat() if self.created_at else None}

class Setting(db.Model):
	__tablename__ = 'settings'
	id = db.Column(db.Integer, primary_key=True)
	key = db.Column(db.String(100), unique=True, nullable=False)
	value = db.Column(db.Text)
	value_type = db.Column(db.String(20), default='string')

	def get_value(self):
		if self.value is None: return None
		t = self.value_type
		if t == 'int': return int(self.value)
		if t == 'float': return float(self.value)
		if t == 'bool': return self.value.lower() in ('true', '1', 'yes')
		if t == 'json': return json.loads(self.value)
		return self.value

	def set_value(self, val):
		type_map = {bool: ('bool', str), int: ('int', str), float: ('float', str)}
		for py_type, (vtype, conv) in type_map.items():
			if isinstance(val, py_type) and not (isinstance(val, bool) and py_type == int):
				self.value_type, self.value = vtype, conv(val); return
		if isinstance(val, (dict, list)):
			self.value_type, self.value = 'json', json.dumps(val)
		else:
			self.value_type, self.value = 'string', str(val)

	@staticmethod
	def get(key, default=None):
		s = Setting.query.filter_by(key=key).first()
		return s.get_value() if s else default

	@staticmethod
	def set(key, value):
		s = Setting.query.filter_by(key=key).first()
		if not s:
			s = Setting(key=key); db.session.add(s)
		s.set_value(value); db.session.commit()

	@staticmethod
	def init_defaults():
		defaults = {
			'playback_speed': Config.DEFAULT_PLAYBACK_SPEED,
			'skip_silence_enabled': Config.DEFAULT_SKIP_SILENCE_ENABLED,
			'skip_silence_db_threshold': Config.DEFAULT_SKIP_SILENCE_DB_THRESHOLD,
			'skip_silence_min_duration': Config.DEFAULT_SKIP_SILENCE_MIN_DURATION,
			'skip_silence_speed': Config.DEFAULT_SKIP_SILENCE_SPEED,
			'subtitle_enabled': Config.DEFAULT_SUBTITLE_ENABLED,
			'rtl_enabled': Config.DEFAULT_RTL_ENABLED,
			'audio_device': Config.DEFAULT_AUDIO_DEVICE,
			'hotkeys': Config.DEFAULT_HOTKEYS,
			'timestamp_template': '[{HH}:{MM}:{SS}]({url})',
			'theater_mode': False,
		}
		for key, value in defaults.items():
			if not Setting.query.filter_by(key=key).first():
				Setting.set(key, value)

class CourseSetting(db.Model):
	__tablename__ = 'course_settings'
	id = db.Column(db.Integer, primary_key=True)
	course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False, unique=True)
	playback_speed = db.Column(db.Float)
	skip_silence_enabled = db.Column(db.Boolean)
	skip_silence_db_threshold = db.Column(db.Integer)
	skip_silence_min_duration = db.Column(db.Float)
	skip_silence_speed = db.Column(db.Float)
	subtitle_enabled = db.Column(db.Boolean)
	rtl_enabled = db.Column(db.Boolean)
	course = db.relationship('Course', back_populates='settings')

	def to_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns
				if c.name not in ('id', 'course_id')}

# ── Setting type map for bulk updates ─────────────────────────────────────────
SETTING_TYPES = {
	'playback_speed': float, 'skip_silence_enabled': bool,
	'skip_silence_db_threshold': int, 'skip_silence_min_duration': float,
	'skip_silence_speed': float, 'subtitle_enabled': bool,
	'rtl_enabled': bool, 'theater_mode': bool, 'timestamp_template': str,
}

# ── File Utilities ─────────────────────────────────────────────────────────────
def get_file_type(extension):
	ext = extension.lower()
	for ext_set, ftype in [(Config.VIDEO_EXTENSIONS, 'video'), (Config.AUDIO_EXTENSIONS, 'audio'),
						   (Config.PDF_EXTENSIONS, 'pdf'), (Config.EPUB_EXTENSIONS, 'epub'),
						   (Config.IMAGE_EXTENSIONS, 'image'),
						   (Config.SUBTITLE_EXTENSIONS, 'subtitle')]:
		if ext in ext_set: return ftype
	return None

def _nat_key(s):
	"""Natural sort key: 'file2' < 'file10'"""
	return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', str(s))]

def get_media_duration(file_path):
	"""Get media file duration in seconds using ffprobe"""
	try:
		import subprocess
		r = subprocess.run(
			['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
			 '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
			capture_output=True, text=True, timeout=5
		)
		if r.returncode == 0 and r.stdout.strip():
			return int(float(r.stdout.strip()))
	except Exception:
		pass
	return None

def extract_video_thumbnail(file_path, output_dir='instance/thumbnails'):
	"""Extract thumbnail from video at 10% duration"""
	try:
		import subprocess
		from pathlib import Path
		
		# Create thumbnails directory
		os.makedirs(output_dir, exist_ok=True)
		
		# Generate thumbnail filename
		file_hash = hashlib.md5(file_path.encode('utf-8')).hexdigest()[:16]
		thumb_filename = f'{file_hash}.jpg'
		thumb_path = os.path.join(output_dir, thumb_filename)
		
		# Check if thumbnail already exists
		if os.path.exists(thumb_path):
			return f'/thumbnails/{thumb_filename}'
		
		# Get video duration
		duration = get_media_duration(file_path)
		if not duration:
			return None
		
		# Extract frame at 10% of video
		timestamp = int(duration * 0.1)
		
		# Run ffmpeg
		subprocess.run([
			'ffmpeg', '-ss', str(timestamp), '-i', file_path,
			'-vframes', '1', '-q:v', '2',
			'-vf', 'scale=320:-1',
			thumb_path
		], capture_output=True, timeout=10, check=False)
		
		if os.path.exists(thumb_path):
			return f'/thumbnails/{thumb_filename}'
		
	except Exception as e:
		print(f"Thumbnail extraction failed for {file_path}: {e}")
	return None

def get_video_quality(file_path):
	"""Get video resolution/quality"""
	try:
		import subprocess
		r = subprocess.run([
			'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
			'-show_entries', 'stream=width,height',
			'-of', 'csv=p=0', file_path
		], capture_output=True, text=True, timeout=5)
		
		if r.returncode == 0 and r.stdout.strip():
			width, height = r.stdout.strip().split(',')
			height = int(height)
			
			# Determine quality label
			if height >= 2160:
				return '4K'
			elif height >= 1440:
				return '1440p'
			elif height >= 1080:
				return '1080p'
			elif height >= 720:
				return '720p'
			elif height >= 480:
				return '480p'
			else:
				return f'{height}p'
	except Exception:
		pass
	return None

def generate_file_hash(file_path, relative_path):
	return hashlib.md5(relative_path.encode('utf-8')).hexdigest()[:16]

def scan_course_folder(course):
	if not os.path.exists(course.root_path):
		course.is_available = False; db.session.commit(); return []
	course.is_available = True
	existing = {f.file_hash: f for f in CourseFile.query.filter_by(course_id=course.id).all()}
	updated_hashes, files_found = set(), []
	for root, dirs, files in os.walk(course.root_path):
		dirs.sort(key=_nat_key); files.sort(key=_nat_key)
		for idx, filename in enumerate(files):
			ext = Path(filename).suffix
			ftype = get_file_type(ext)
			if not ftype: continue
			file_path = os.path.join(root, filename)
			rel_path = os.path.relpath(file_path, course.root_path)
			parent = os.path.relpath(root, course.root_path)
			parent = None if parent == '.' else parent
			try: fsize = os.path.getsize(file_path)
			except: fsize = 0
			fhash = generate_file_hash(file_path, rel_path)
			updated_hashes.add(fhash)
			if fhash in existing:
				cf = existing[fhash]
				cf.file_path, cf.relative_path, cf.file_name = file_path, rel_path, filename
				cf.file_size, cf.parent_folder, cf.order_index = fsize, parent, idx
				if cf.duration is None and ftype in ('video','audio'):
					cf.duration = get_media_duration(file_path)
				# Extract thumbnail for videos
				if ftype == 'video' and not cf.thumbnail:
					thumb = extract_video_thumbnail(file_path)
					if thumb:
						cf.thumbnail = thumb
				# Get video quality
				if ftype == 'video' and not cf.video_quality:
					cf.video_quality = get_video_quality(file_path)
			else:
				dur = get_media_duration(file_path) if ftype in ('video','audio') else None
				thumb = extract_video_thumbnail(file_path) if ftype == 'video' else None
				quality = get_video_quality(file_path) if ftype == 'video' else None
				cf = CourseFile(file_hash=fhash, course_id=course.id, file_path=file_path,
					relative_path=rel_path, file_name=filename, file_type=ftype,
					file_extension=ext, file_size=fsize, duration=dur,
					thumbnail=thumb, video_quality=quality,
					parent_folder=parent, order_index=idx)
				db.session.add(cf)
			files_found.append(cf)
	for fh, fo in existing.items():
		if fh not in updated_hashes: db.session.delete(fo)
	course.total_files = len(files_found); db.session.commit()
	return files_found

def check_drive_availability():
	for course in Course.query.all():
		avail = os.path.exists(course.root_path)
		if course.is_available != avail:
			course.is_available = avail
			print(f"Course '{course.display_name}' is now {'available' if avail else 'unavailable'}")
	db.session.commit()

def format_duration(seconds):
	if not seconds: return "00:00"
	h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
	return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def format_file_size(bytes_size):
	if not bytes_size: return "0 B"
	units = ['B', 'KB', 'MB', 'GB', 'TB']
	i, size = 0, float(bytes_size)
	while size >= 1024 and i < len(units) - 1: size /= 1024; i += 1
	return f"{size:.2f} {units[i]}"

def get_folder_structure(course_id):
	"""Build nested folder tree with duration stats"""
	files = CourseFile.query.filter_by(course_id=course_id).order_by(CourseFile.relative_path).all()
	plist = PlaybackProgress.query.filter_by(course_id=course_id).all()
	pmap = {p.file_id: p for p in plist}
	wids = set(p.file_id for p in plist if p.completed)
	def _n(name, path):
		return {'name': name, 'path': path, 'children': [], 'files': [],
				'total_duration': 0, 'watched_duration': 0, 'file_count': 0}
	root = _n('Root', '')
	for f in files:
		parts = Path(f.relative_path).parts
		cur = root
		for part in parts[:-1]:
			found = next((c for c in cur['children'] if c['name'] == part), None)
			if not found:
				cp = part if not cur['path'] else cur['path'] + '/' + part
				found = _n(part, cp); cur['children'].append(found)
			cur = found
		cur['files'].append(f)
		dur = f.duration or 0; cur['total_duration'] += dur; cur['file_count'] += 1
		p = pmap.get(f.id)
		if p and p.completed: cur['watched_duration'] += dur
	def _calc(n):
		for c in n['children']:
			_calc(c)
			n['total_duration'] += c['total_duration']
			n['watched_duration'] += c['watched_duration']
			n['file_count'] += c['file_count']
	_calc(root)
	return root, pmap, wids

def tree_to_json(node):
	return {'name': node['name'], 'path': node['path'],
			'children': [tree_to_json(c) for c in node['children']],
		'files': [{'id': f.id, 'file_hash': f.file_hash, 'file_name': f.file_name,
				   'display_name': f.display_name or f.file_name,
				   'file_type': f.file_type, 'duration': f.duration or 0,
				   'file_size': f.file_size, 'parent_folder': f.parent_folder} for f in node['files']],
			'total_duration': node['total_duration'], 'watched_duration': node['watched_duration'],
			'file_count': node['file_count']}

def format_duration_human(seconds):
	if not seconds: return "0m"
	h, m = int(seconds // 3600), int((seconds % 3600) // 60)
	if h and m: return f"{h}h {m}m"
	if h: return f"{h}h"
	return f"{m}m"

def generate_timestamp_link(timestamp, file_id, template=None):
	if template is None:
		template = Setting.get('timestamp_template', '[{HH}:{MM}:{SS}]({url})')
	h, m, s = int(timestamp // 3600), int((timestamp % 3600) // 60), int(timestamp % 60)
	url = f"/player/{file_id}?t={int(timestamp)}"
	return template.replace('{HH}', f'{h:02d}').replace('{MM}', f'{m:02d}').replace('{SS}', f'{s:02d}').replace('{url}', url).replace('{timestamp}', str(int(timestamp)))

def get_course_theme(course):
	"""Get theme for course based on priority: Creator > Category > Tag"""
	# Priority 1: First creator's theme
	if course.creators:
		for creator in course.creators:
			if creator.theme:
				return creator.theme
	
	# Priority 2: First category's theme
	if course.categories:
		for category in course.categories:
			if category.theme:
				return category.theme
	
	# Priority 3: First tag's theme
	if course.tags:
		for tag in course.tags:
			if tag.theme:
				return tag.theme
	
	# Priority 4: Course's own theme
	if course.theme:
		return course.theme
	
	return 'default'

# ── Background Services ────────────────────────────────────────────────────────
_drive_monitor_thread = _hotkey_thread = _observer = None

class DriveMonitor:
	def __init__(self, app): self.app = app
	def on_created(self, event):
		from flask import app as _; import app as _a # force ctx
		with self.app.app_context(): check_drive_availability()
	def on_deleted(self, event):
		with self.app.app_context(): check_drive_availability()

def _drive_monitor_worker(app):
	global _observer
	if os.name == 'nt':
		while True:
			with app.app_context(): check_drive_availability()
			time.sleep(5)
	else:
		from watchdog.observers import Observer
		from watchdog.events import FileSystemEventHandler
		class Handler(FileSystemEventHandler):
			def __init__(self, app): self.app = app
			def on_created(self, e):
				with self.app.app_context(): check_drive_availability()
			def on_deleted(self, e):
				with self.app.app_context(): check_drive_availability()
		_observer = Observer()
		handler = Handler(app)
		for mp in ['/media', '/mnt']:
			if os.path.exists(mp): _observer.schedule(handler, mp, recursive=True)
		_observer.start()
		while True:
			with app.app_context(): check_drive_availability()
			time.sleep(10)

def start_drive_monitor(app):
	global _drive_monitor_thread
	if _drive_monitor_thread is None or not _drive_monitor_thread.is_alive():
		_drive_monitor_thread = threading.Thread(target=_drive_monitor_worker, args=(app,), daemon=True)
		_drive_monitor_thread.start(); print("Drive monitor started")

def start_hotkey_listener(app):
	"""No-op: hotkeys handled by external AHK script calling /api/hotkey/<action>"""
	pass

# ── Database Migration ─────────────────────────────────────────────────────────
def migrate_db():
	"""Auto-migrate: add missing columns"""
	import sqlite3
	db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
	if not os.path.exists(db_path): return
	conn = sqlite3.connect(db_path)
	cur = conn.cursor()
	try:
		# CourseFile migrations
		cur.execute("PRAGMA table_info(course_files)")
		cols = [c[1] for c in cur.fetchall()]
		if 'file_hash' not in cols:
			cur.execute("ALTER TABLE course_files ADD COLUMN file_hash VARCHAR(16)")
			cur.execute("SELECT id, relative_path FROM course_files")
			for fid, rp in cur.fetchall():
				h = hashlib.md5(rp.encode('utf-8')).hexdigest()[:16]
				cur.execute("UPDATE course_files SET file_hash=? WHERE id=?", (h, fid))
		if 'thumbnail' not in cols:
			cur.execute("ALTER TABLE course_files ADD COLUMN thumbnail VARCHAR(512)")
		if 'video_quality' not in cols:
			cur.execute("ALTER TABLE course_files ADD COLUMN video_quality VARCHAR(20)")
		
		# Course migrations
		cur.execute("PRAGMA table_info(courses)")
		cols = [c[1] for c in cur.fetchall()]
		if 'description' not in cols:
			cur.execute("ALTER TABLE courses ADD COLUMN description TEXT")
		if 'theme' not in cols:
			cur.execute("ALTER TABLE courses ADD COLUMN theme VARCHAR(50)")
		
		# CourseSetting migrations
		cur.execute("PRAGMA table_info(course_settings)")
		cols = [c[1] for c in cur.fetchall()]
		if 'skip_silence_speed' not in cols:
			cur.execute("ALTER TABLE course_settings ADD COLUMN skip_silence_speed FLOAT")
		
		conn.commit()
	except Exception as e:
		print(f"Migration note: {e}"); conn.rollback()
	finally: conn.close()
