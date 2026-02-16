import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    import uvicorn
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    port = int(os.environ.get('PORT', 5005))
    uvicorn.run('main:app', host='0.0.0.0', port=port, reload=debug)
