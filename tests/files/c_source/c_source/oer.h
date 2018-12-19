/**
 * The MIT License (MIT)
 *
 * Copyright (c) 2018 Erik Moqvist
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

/**
 * This file was generated by asn1tools version 0.137.4 Thu Dec 13 05:47:38 2018.
 */

#ifndef OER_H
#define OER_H

#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>

#ifndef ENOMEM
#    define ENOMEM 12
#endif

#ifndef EINVAL
#    define EINVAL 22
#endif

#ifndef EOUTOFDATA
#    define EOUTOFDATA 500
#endif

#ifndef EBADCHOICE
#    define EBADCHOICE 501
#endif

#ifndef EBADLENGTH
#    define EBADLENGTH 502
#endif

struct oer_c_source_a_t {
    int8_t a;
    int16_t b;
    int32_t c;
    int64_t d;
    uint8_t e;
    uint16_t f;
    uint32_t g;
    uint64_t h;
    float i;
    double j;
    bool k;
    uint8_t l[11];
};

enum oer_c_source_b_choice_t {
    oer_c_source_b_choice_a_t = 0,
    oer_c_source_b_choice_b_t
};

struct oer_c_source_b_t {
    enum oer_c_source_b_choice_t choice;
    union {
        int8_t a;
        struct oer_c_source_a_t b;
    } value;
};

struct oer_c_source_c_t {
    uint8_t length;
    struct oer_c_source_b_t elements[2];
};

enum oer_c_source_d_a_b_choice_t {
    oer_c_source_d_a_b_choice_c_t = 0,
    oer_c_source_d_a_b_choice_d_t
};

enum oer_c_source_d_f_g_t {
    oer_c_source_d_f_g_h_t = 0,
    oer_c_source_d_f_g_i_t,
    oer_c_source_d_f_g_j_t
};

struct oer_c_source_d_a_t {
    struct {
        enum oer_c_source_d_a_b_choice_t choice;
        union {
            uint8_t c;
            bool d;
        } value;
    } b;
    struct {
        uint8_t length;
    } e;
};

struct oer_c_source_d_t {
    uint8_t length;
    struct {
        struct {
            struct {
                enum oer_c_source_d_a_b_choice_t choice;
                union {
                    uint8_t c;
                    bool d;
                } value;
            } b;
            struct {
                uint8_t length;
            } e;
        } a;
        struct {
            enum oer_c_source_d_f_g_t g;
            struct {
                uint8_t length;
                uint8_t value[2];
            } k;
        } f;
        struct {
            bool is_m_present;
            bool m;
            int8_t n;
            bool is_o_present;
            struct {
                uint8_t p[5];
                bool is_q_present;
                bool q;
            } o;
        } l;
    } elements[10];
};

struct oer_programming_types_bool_t {
    bool value;
};

struct oer_programming_types_double_t {
    double value;
};

struct oer_programming_types_float_t {
    float value;
};

struct oer_programming_types_int16_t {
    int16_t value;
};

struct oer_programming_types_int32_t {
    int32_t value;
};

struct oer_programming_types_int64_t {
    int64_t value;
};

struct oer_programming_types_int8_t {
    int8_t value;
};

struct oer_programming_types_uint16_t {
    uint16_t value;
};

struct oer_programming_types_uint32_t {
    uint32_t value;
};

struct oer_programming_types_uint64_t {
    uint64_t value;
};

struct oer_programming_types_uint8_t {
    uint8_t value;
};

ssize_t oer_c_source_a_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_c_source_a_t *src_p);

ssize_t oer_c_source_a_decode(
    struct oer_c_source_a_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_c_source_b_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_c_source_b_t *src_p);

ssize_t oer_c_source_b_decode(
    struct oer_c_source_b_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_c_source_c_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_c_source_c_t *src_p);

ssize_t oer_c_source_c_decode(
    struct oer_c_source_c_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_c_source_d_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_c_source_d_t *src_p);

ssize_t oer_c_source_d_decode(
    struct oer_c_source_d_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_programming_types_bool_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_programming_types_bool_t *src_p);

ssize_t oer_programming_types_bool_decode(
    struct oer_programming_types_bool_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_programming_types_double_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_programming_types_double_t *src_p);

ssize_t oer_programming_types_double_decode(
    struct oer_programming_types_double_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_programming_types_float_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_programming_types_float_t *src_p);

ssize_t oer_programming_types_float_decode(
    struct oer_programming_types_float_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_programming_types_int16_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_programming_types_int16_t *src_p);

ssize_t oer_programming_types_int16_decode(
    struct oer_programming_types_int16_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_programming_types_int32_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_programming_types_int32_t *src_p);

ssize_t oer_programming_types_int32_decode(
    struct oer_programming_types_int32_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_programming_types_int64_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_programming_types_int64_t *src_p);

ssize_t oer_programming_types_int64_decode(
    struct oer_programming_types_int64_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_programming_types_int8_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_programming_types_int8_t *src_p);

ssize_t oer_programming_types_int8_decode(
    struct oer_programming_types_int8_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_programming_types_uint16_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_programming_types_uint16_t *src_p);

ssize_t oer_programming_types_uint16_decode(
    struct oer_programming_types_uint16_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_programming_types_uint32_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_programming_types_uint32_t *src_p);

ssize_t oer_programming_types_uint32_decode(
    struct oer_programming_types_uint32_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_programming_types_uint64_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_programming_types_uint64_t *src_p);

ssize_t oer_programming_types_uint64_decode(
    struct oer_programming_types_uint64_t *dst_p,
    const uint8_t *src_p,
    size_t size);

ssize_t oer_programming_types_uint8_encode(
    uint8_t *dst_p,
    size_t size,
    const struct oer_programming_types_uint8_t *src_p);

ssize_t oer_programming_types_uint8_decode(
    struct oer_programming_types_uint8_t *dst_p,
    const uint8_t *src_p,
    size_t size);

#endif
