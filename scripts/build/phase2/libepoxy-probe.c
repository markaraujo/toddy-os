/* Native Epoxy dispatch over installed Mesa EGL/GLES; no window/hardware claim. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <epoxy/egl.h>
#include <epoxy/gl.h>

static GLuint shader(GLenum type,const char *source) {
    GLuint result=glCreateShader(type); assert(result);
    glShaderSource(result,1,&source,NULL);glCompileShader(result);
    GLint ok=0;glGetShaderiv(result,GL_COMPILE_STATUS,&ok);
    if(!ok){char log[4096];glGetShaderInfoLog(result,sizeof(log),NULL,log);fprintf(stderr,"%s\n",log);exit(2);}
    return result;
}

int main(void) {
    PFNEGLGETPLATFORMDISPLAYEXTPROC get_display=(PFNEGLGETPLATFORMDISPLAYEXTPROC)eglGetProcAddress("eglGetPlatformDisplayEXT");
    assert(get_display);
    EGLDisplay display=get_display(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,NULL);
    assert(display!=EGL_NO_DISPLAY);
    EGLint major=0,minor=0;assert(eglInitialize(display,&major,&minor));
    assert(major>=1 && eglBindAPI(EGL_OPENGL_ES_API));
    EGLint attributes[]={EGL_SURFACE_TYPE,EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_NONE};
    EGLConfig config;EGLint count=0;assert(eglChooseConfig(display,attributes,&config,1,&count) && count==1);
    EGLint surface_attributes[]={EGL_WIDTH,32,EGL_HEIGHT,32,EGL_NONE};
    EGLSurface surface=eglCreatePbufferSurface(display,config,surface_attributes);assert(surface!=EGL_NO_SURFACE);
    EGLint context_attributes[]={EGL_CONTEXT_CLIENT_VERSION,2,EGL_NONE};
    EGLContext context=eglCreateContext(display,config,EGL_NO_CONTEXT,context_attributes);assert(context!=EGL_NO_CONTEXT);
    assert(eglMakeCurrent(display,surface,surface,context));
    assert(epoxy_has_egl() && epoxy_egl_version(display)>=15 && epoxy_gl_version()>=20 && !epoxy_is_desktop_gl());
    const char *renderer=(const char *)glGetString(GL_RENDERER);assert(renderer && strstr(renderer,"llvmpipe"));
    GLuint vertex=shader(GL_VERTEX_SHADER,"attribute vec2 position;void main(){gl_Position=vec4(position,0.0,1.0);}");
    GLuint fragment=shader(GL_FRAGMENT_SHADER,"precision mediump float;void main(){gl_FragColor=vec4(0.0,0.125490196,0.250980392,1.0);}");
    GLuint program=glCreateProgram();assert(program);glAttachShader(program,vertex);glAttachShader(program,fragment);
    glBindAttribLocation(program,0,"position");glLinkProgram(program);
    GLint linked=0;glGetProgramiv(program,GL_LINK_STATUS,&linked);assert(linked);
    glUseProgram(program);glViewport(0,0,32,32);glClearColor(1,0,1,1);glClear(GL_COLOR_BUFFER_BIT);
    const GLfloat vertices[]={-1,-1,3,-1,-1,3};
    glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,0,vertices);glEnableVertexAttribArray(0);
    glDrawArrays(GL_TRIANGLES,0,3);glFinish();assert(glGetError()==GL_NO_ERROR);
    GLubyte pixel[4]={255,0,0,0};glReadPixels(16,16,1,1,GL_RGBA,GL_UNSIGNED_BYTE,pixel);
    assert(glGetError()==GL_NO_ERROR && pixel[0]==0 && abs((int)pixel[1]-32)<=1 && abs((int)pixel[2]-64)<=1 && pixel[3]==255);
    printf("renderer: %s\negl: %d.%d\npixel: %u %u %u %u\n",renderer,major,minor,pixel[0],pixel[1],pixel[2],pixel[3]);
    glDeleteProgram(program);glDeleteShader(vertex);glDeleteShader(fragment);
    assert(eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT));
    assert(eglDestroyContext(display,context) && eglDestroySurface(display,surface) && eglTerminate(display));
    return 0;
}
