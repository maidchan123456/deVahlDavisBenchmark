// Independent array canonicalization only; no scientific arithmetic/reduction.
#include <Python.h>
#include <vector>
#include <map>
#include <sstream>
#include <iomanip>
#include <cmath>
#include <cstring>
#include <functional>
#include <charconv>
static PyObject* canonical(PyObject*,PyObject* args){Py_buffer view;PyObject* dims;if(!PyArg_ParseTuple(args,"y*O",&view,&dims))return nullptr;
 std::vector<size_t> shape;size_t count=1;PyObject* seq=PySequence_Fast(dims,"shape required");if(!seq){PyBuffer_Release(&view);return nullptr;}for(Py_ssize_t i=0;i<PySequence_Fast_GET_SIZE(seq);i++){size_t n=PyLong_AsSize_t(PySequence_Fast_GET_ITEM(seq,i));if(PyErr_Occurred()||n==0||n>size_t(view.len/8)||count>size_t(view.len/8)/n){Py_DECREF(seq);PyBuffer_Release(&view);if(!PyErr_Occurred())PyErr_SetString(PyExc_ValueError,"SHAPE");return nullptr;}shape.push_back(n);count*=n;}Py_DECREF(seq);if(shape.empty()||count*8!=size_t(view.len)){PyBuffer_Release(&view);PyErr_SetString(PyExc_ValueError,"LENGTH");return nullptr;}
 std::string result;bool finite=true;
 Py_BEGIN_ALLOW_THREADS
 {std::string out;out.reserve(count*4);std::map<uint64_t,std::string> tokens;size_t offset=0;
  std::function<void(size_t)> emit=[&](size_t rank){out+='[';for(size_t i=0;i<shape[rank];i++){if(i)out+=',';if(rank+1<shape.size())emit(rank+1);else{double v;std::memcpy(&v,static_cast<const char*>(view.buf)+offset*8,8);offset++;if(!std::isfinite(v)){finite=false;continue;}uint64_t bits;std::memcpy(&bits,&v,8);auto hit=tokens.find(bits);if(hit!=tokens.end())out+=hit->second;else{char buffer[128];std::string text;if(v==0&&std::signbit(v))text="-0.0";else{auto converted=std::to_chars(buffer,buffer+128,v,std::chars_format::general,17);text.assign(buffer,converted.ptr);}out+=text;if(tokens.size()<128)tokens.emplace(bits,text);}}}out+=']';};emit(0);result=std::move(out);}
 Py_END_ALLOW_THREADS
 PyBuffer_Release(&view);if(!finite){PyErr_SetString(PyExc_ValueError,"NONFINITE_PAYLOAD");return nullptr;}return PyUnicode_DecodeUTF8(result.data(),result.size(),"strict");
}
static PyMethodDef methods[]={{"canonical",canonical,METH_VARARGS,"Canonical IEEE64 arrays; releases GIL; ordered result."},{nullptr,nullptr,0,nullptr}};
static PyModuleDef module={PyModuleDef_HEAD_INIT,"numeric_parallel",nullptr,-1,methods};
PyMODINIT_FUNC PyInit_numeric_parallel(){return PyModule_Create(&module);}
