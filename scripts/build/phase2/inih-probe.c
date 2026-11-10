/* C callback and C++ parser ABI, UTF8/defaults/refusal/recovery. Compiled as C++. */
#include <ini.h>
#include <INIReader.h>
#include <cassert>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
struct Seen {bool name=false;};
static int handler(void *p,const char *section,const char *name,const char *value) {
 if(std::strcmp(section,"Owner")==0 && std::strcmp(name,"name")==0){assert(std::strcmp(value,"Toddy ã")==0);static_cast<Seen*>(p)->name=true;}return 1;
}
int main(int argc,char **argv) {
 assert(argc==2);std::string base=argv[1];
 for(int i=0;i<2;i++) {
  auto good=base+"/good-"+std::to_string(i)+".ini",bad=base+"/bad-"+std::to_string(i)+".ini";
  {std::ofstream f(good);f<<"[Owner]\nname=Toddy ã\nactive=yes\ncount=42\n";}
  Seen seen;assert(ini_parse(good.c_str(),handler,&seen)==0 && seen.name);
  INIReader reader(good);assert(reader.ParseError()==0);assert(reader.Get("Owner","name","")=="Toddy ã");assert(reader.GetBoolean("Owner","active",false));assert(reader.GetInteger("Owner","count",0)==42);assert(reader.Get("Owner","missing","fallback")=="fallback");
  {std::ofstream f(bad);f<<"[Owner\n";}
  INIReader invalid(bad);assert(invalid.ParseError()>0);assert(reader.Get("Owner","name","")=="Toddy ã");
  INIReader recovery(good);assert(recovery.ParseError()==0 && recovery.GetInteger("Owner","count",0)==42);
 }
 std::cout<<"{\"C_and_Cpp_UTF8_parse_cycles\":2,\"typed_and_missing_defaults\":true,\"malformed_refusals\":2,\"prior_state_retained\":true,\"recovery_cycles\":2}\n";
}
