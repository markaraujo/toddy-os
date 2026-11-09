// Real dynamically linked embedding consumer; no shell or mocked JS engine.
#include <cassert>
#include <cstring>
#include <iostream>
#include <jsapi.h>
#include <js/CompilationAndEvaluation.h>
#include <js/Context.h>
#include <js/Exception.h>
#include <js/GlobalObject.h>
#include <js/Initialization.h>
#include <js/Realm.h>
#include <js/SourceText.h>

static bool evaluate(JSContext* cx, const char* text, JS::MutableHandleValue value) {
  JS::CompileOptions options(cx);
  options.setFileAndLine("toddy-native-embedding", 1);
  JS::SourceText<mozilla::Utf8Unit> source;
  if (!source.init(cx, text, std::strlen(text), JS::SourceOwnership::Borrowed))
    return false;
  return JS::Evaluate(cx, options, source, value);
}

int main() {
  assert(JS_Init());
  JSContext* cx = JS_NewContext(64 * 1024 * 1024);
  assert(cx && JS::InitSelfHostedCode(cx));
  {
    static const JSClass global_class = {
      "ToddyEmbedding", JSCLASS_GLOBAL_FLAGS, &JS::DefaultGlobalClassOps,
      nullptr, nullptr, nullptr
    };
    JS::RealmOptions options;
    JS::RootedObject global(cx, JS_NewGlobalObject(cx, &global_class, nullptr,
                              JS::FireOnNewGlobalHook, options));
    assert(global);
    JSAutoRealm realm(cx, global);
    assert(JS::InitRealmStandardClasses(cx));
    JS::RootedValue value(cx);
    assert(evaluate(cx, "new Int32Array([6,7]).reduce((a,b)=>a*b)", &value));
    assert(value.isNumber() && value.toNumber() == 42);
    assert(evaluate(cx, "globalThis.saved={text:'a\\u00e7\\u00e3o',value:42};true", &value));
    JS_GC(cx);
    assert(evaluate(cx, "saved.value===42 && saved.text==='a\\u00e7\\u00e3o' && 'a\\u0301'.normalize('NFC')==='\\u00e1' && new Intl.Collator('pt').compare('a','b')<0", &value));
    assert(value.isBoolean() && value.toBoolean());
    assert(!evaluate(cx, "function {", &value));
    assert(JS_IsExceptionPending(cx));
    JS_ClearPendingException(cx);
    assert(evaluate(cx, "40+2", &value));
    assert(value.isNumber() && value.toNumber() == 42);
  }
  JS_DestroyContext(cx);
  JS_ShutDown();
  std::cout << "dynamic embedding: typed array/GC/Unicode/Intl/refusal/recovery=42\n";
}
