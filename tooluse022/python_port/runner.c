/* Bounded Python3 subset. No filesystem/network/process/native-code bindings.
 * MicroPython is MIT; see the retained upstream license and source hashes.
 * Each request starts a fresh16MiB VM. Android runs this in an isolated service.
 */
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include "py/compile.h"
#include "py/builtin.h"
#include "py/objmodule.h"
#include "py/runtime.h"
#include "py/gc.h"
#include "py/stackctrl.h"
#include "port/micropython_embed.h"
static char heap[16*1024*1024];
static char output[7000];
static size_t used;
static unsigned long fuel;
static jmp_buf escape;
static struct timespec started;
static int success;
static mp_obj_t denied_open(size_t n_args,const mp_obj_t *args,mp_map_t *kw) {
    (void)n_args;(void)args;(void)kw;mp_raise_msg(&mp_type_OSError,MP_ERROR_TEXT("filesystem unavailable"));
}
MP_DEFINE_CONST_FUN_OBJ_KW(mp_builtin_open_obj,0,denied_open);
void liquid_vm_tick(void) {
    if (++fuel > 2000000) longjmp(escape,1);
    if ((fuel & 1023)==0) {
        struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t);
        if ((t.tv_sec-started.tv_sec)+(t.tv_nsec-started.tv_nsec)*1e-9 > 2.0) longjmp(escape,1);
    }
}
void mp_hal_stdout_tx_strn_cooked(const char *s,size_t n) {
    if (used+n>6000) longjmp(escape,2);
    memcpy(output+used,s,n);used+=n;output[used]=0;
}
static int execute(const char *s) {
    nlr_buf_t nlr;
    if (nlr_push(&nlr)==0) {
        mp_lexer_t *lex=mp_lexer_new_from_str_len(MP_QSTR__lt_stdin_gt_,s,strlen(s),0);
        qstr source=lex->source_name;mp_parse_tree_t tree=mp_parse(lex,MP_PARSE_FILE_INPUT);
        mp_obj_t f=mp_compile(&tree,source,true);mp_call_function_0(f);nlr_pop();return 1;
    }
    mp_obj_print_exception(&mp_plat_print,(mp_obj_t)nlr.ret_val);return 0;
}
static void math_helpers(void) {
    // Make a fresh mutable copy of the real builtin math module. The three
    // supplemental functions perform actual integer arithmetic in Python.
    mp_obj_module_t *old=MP_OBJ_TO_PTR(mp_module_get_builtin(MP_QSTR_math,false));
    mp_obj_module_t *fresh=MP_OBJ_TO_PTR(mp_obj_new_module(MP_QSTR_math));
    for(size_t i=0;i<old->globals->map.alloc;i++) {
        mp_map_elem_t *el=&old->globals->map.table[i];
        if(mp_map_slot_is_filled(&old->globals->map,i))mp_obj_dict_store(MP_OBJ_FROM_PTR(fresh->globals),el->key,el->value);
    }
    if (!execute("import math\n"
      "def _gcd(a,b):\n a,b=abs(a),abs(b)\n while b:\n  a,b=b,a%b\n return a\n"
      "def _isqrt(n):\n if n<0: raise ValueError('negative isqrt')\n if n<2: return n\n x=n\n y=(x+1)//2\n while y<x:\n  x=y\n  y=(x+n//x)//2\n return x\n"
      "def _lcm(a,b):\n return abs(a//_gcd(a,b)*b) if a and b else 0\n"
      "math.gcd=_gcd\nmath.isqrt=_isqrt\nmath.lcm=_lcm\n"))longjmp(escape,3);
}
// Single-threaded isolated service calls only. Returns stdout or the actual
// exception text; status is a separate field, never inferred from the text.
const char *liquid_python_run(const char *code) {
    used=0;output[0]=0;fuel=0;success=0;clock_gettime(CLOCK_MONOTONIC,&started);
    int jump=setjmp(escape);
    if(jump) {
        const char *error=jump==1?"ResourceLimit: time or instruction budget":jump==2?"ResourceLimit: stdout budget":"RuntimeError: math helper initialization";
        snprintf(output,sizeof(output),"%s",error);return output;
    }
    int stack_top;mp_embed_init(heap,sizeof(heap),&stack_top);mp_stack_set_limit(128*1024);
    math_helpers();used=0;output[0]=0;
    success=execute(code);mp_embed_deinit();return output;
}
int liquid_python_ok(void) {return success;}
#if defined(__ANDROID__)
#include <jni.h>
JNIEXPORT jbyteArray JNICALL Java_dev_liquidsense_chat_PythonService_nativeRun(JNIEnv *env,jclass cls,jbyteArray input) {
    (void)cls;jsize n=(*env)->GetArrayLength(env,input);if(n>6000)return NULL;
    char source[6001];(*env)->GetByteArrayRegion(env,input,0,n,(jbyte*)source);source[n]=0;
    const char *out=liquid_python_run(source);size_t len=strlen(out);jbyteArray result=(*env)->NewByteArray(env,len+1);
    jbyte ok=liquid_python_ok()?1:0;(*env)->SetByteArrayRegion(env,result,0,1,&ok);(*env)->SetByteArrayRegion(env,result,1,len,(const jbyte*)out);return result;
}
#else
int main(void) {
    char source[6002];size_t n=fread(source,1,6001,stdin);if(n>6000)return 3;source[n]=0;
    const char *out=liquid_python_run(source);fputs(out,stdout);return liquid_python_ok()?0:1;
}
#endif
