from fastapi import APIRouter, Request, HTTPException
from app.templating import templates

router = APIRouter(prefix='/blog')


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


@router.get('/', name='blog.index')
async def index(request: Request):
    """Blog listing page."""
    return templates.TemplateResponse(request, 'blog/index.html', {'posts': POSTS})


@router.get('/{slug}', name='blog.post')
async def post(request: Request, slug: str):
    """Individual blog post page."""
    post = get_post_by_slug(slug)
    if post is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(request, 'blog/post.html', {'post': post})
