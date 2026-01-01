from flask import Blueprint, render_template, abort

bp = Blueprint('blog', __name__, url_prefix='/blog')


# Blog posts data - replace with database later
# Posts are ordered newest first
POSTS = [
    {
        'slug': 'welcome-to-my-blog',
        'title': 'Welcome to My Blog',
        'date': '2026-01-01',
        'summary': 'An introduction to my new blog where I share thoughts on technology and projects.',
        'content': '''
Welcome to my blog! This is where I'll be sharing my thoughts on technology,
projects I'm working on, and things I find interesting.

Stay tuned for more posts coming soon.
        '''.strip()
    },
]


def get_post_by_slug(slug):
    """Find a post by its slug."""
    for post in POSTS:
        if post['slug'] == slug:
            return post
    return None


@bp.route('/')
def index():
    """Blog listing page."""
    return render_template('blog/index.html', posts=POSTS)


@bp.route('/<slug>')
def post(slug):
    """Individual blog post page."""
    post = get_post_by_slug(slug)
    if post is None:
        abort(404)
    return render_template('blog/post.html', post=post)
