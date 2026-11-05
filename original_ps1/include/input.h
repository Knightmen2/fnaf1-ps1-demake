#ifndef FNAF_INPUT_H
#define FNAF_INPUT_H

void input_init_ps1(void);
void input_poll(void);
unsigned short input_read_raw(void);
unsigned short input_map(unsigned short raw_btn_active_low);

#endif
