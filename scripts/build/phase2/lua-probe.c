#include <assert.h>
#include <lua.h>
#include <lauxlib.h>
#include <lualib.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    assert(strcmp(LUA_RELEASE, "Lua 5.4.8") == 0);
    lua_State *state = luaL_newstate();
    assert(state);
    luaL_openlibs(state);
    assert(luaL_dostring(state, "local t={3,1,2}; table.sort(t); assert(table.concat(t)== '123'); return 6*7") == LUA_OK);
    assert(lua_isinteger(state, -1) && lua_tointeger(state, -1) == 42);
    lua_pop(state, 1);
    assert(luaL_loadstring(state, "error('toddy expected failure')") == LUA_OK);
    assert(lua_pcall(state, 0, LUA_MULTRET, 0) == LUA_ERRRUN);
    assert(strstr(lua_tostring(state, -1), "toddy expected failure"));
    lua_pop(state, 1);
    assert(lua_gettop(state) == 0);
    lua_close(state);
    puts("native Lua5.4.8 shared C API/table sorting/integer result/protected error/stack cleanup");
    return 0;
}
