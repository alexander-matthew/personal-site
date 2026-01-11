from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(UserMixin, db.Model):
    """User account for goal tracking."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    categories = db.relationship('Category', backref='user', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Category(db.Model):
    """Goal categories (preset or user-defined)."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#60a5fa')  # Hex color
    is_preset = db.Column(db.Boolean, default=False)

    # Relationships
    goals = db.relationship('Goal', backref='category', lazy=True)

    # Preset categories to create for new users
    PRESETS = [
        {'name': 'Health', 'color': '#22c55e'},
        {'name': 'Career', 'color': '#3b82f6'},
        {'name': 'Finance', 'color': '#eab308'},
        {'name': 'Learning', 'color': '#a855f7'},
        {'name': 'Personal', 'color': '#ec4899'},
        {'name': 'Relationships', 'color': '#f97316'},
    ]

    @classmethod
    def create_presets_for_user(cls, user_id):
        """Create preset categories for a new user."""
        for preset in cls.PRESETS:
            category = cls(
                user_id=user_id,
                name=preset['name'],
                color=preset['color'],
                is_preset=True
            )
            db.session.add(category)


class Goal(db.Model):
    """Individual goal with progress tracking."""
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Goal type: 'one_time', 'streak', 'periodic'
    goal_type = db.Column(db.String(20), default='one_time')

    # Progress type: 'binary' or 'percentage'
    progress_type = db.Column(db.String(20), default='binary')

    # For percentage goals (e.g., "Read 24 books")
    target_value = db.Column(db.Integer, default=1)
    current_value = db.Column(db.Integer, default=0)

    # Frequency for recurring goals: 'daily', 'weekly', 'monthly', null
    frequency = db.Column(db.String(20), nullable=True)

    # Priority: 'normal' or 'stretch'
    priority = db.Column(db.String(20), default='normal')

    # Dates
    deadline = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    progress_logs = db.relationship('ProgressLog', backref='goal', lazy=True, cascade='all, delete-orphan')

    @property
    def is_completed(self):
        """Check if goal is completed."""
        if self.progress_type == 'binary':
            return self.completed_at is not None
        return self.current_value >= self.target_value

    @property
    def progress_percent(self):
        """Get progress as percentage (0-100)."""
        if self.progress_type == 'binary':
            return 100 if self.is_completed else 0
        if self.target_value == 0:
            return 0
        return min(100, int((self.current_value / self.target_value) * 100))

    @property
    def current_streak(self):
        """Calculate current streak for streak-type goals."""
        if self.goal_type != 'streak':
            return 0

        logs = ProgressLog.query.filter_by(goal_id=self.id).order_by(
            ProgressLog.logged_at.desc()
        ).all()

        if not logs:
            return 0

        streak = 0
        today = datetime.now(timezone.utc).date()

        for i, log in enumerate(logs):
            log_date = log.logged_at.date()
            expected_date = today if i == 0 else (today - timedelta(days=i))

            # Allow for yesterday if today hasn't been logged yet
            if i == 0 and log_date == today - timedelta(days=1):
                expected_date = today - timedelta(days=1)

            if log_date == expected_date:
                streak += 1
            else:
                break

        return streak


class ProgressLog(db.Model):
    """Log entry for goal progress updates."""
    __tablename__ = 'progress_logs'

    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    logged_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    value = db.Column(db.Integer, default=1)  # Amount added (for percentage) or 1 (for check-in)
    note = db.Column(db.String(500), nullable=True)


# Import timedelta for streak calculation
from datetime import timedelta
