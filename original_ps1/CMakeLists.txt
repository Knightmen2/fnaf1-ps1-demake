cmake_minimum_required(VERSION 3.21)

project(
	fnaf1_ps1
	LANGUAGES C ASM
	VERSION 0.2.2
	DESCRIPTION "FNAF 1 demake for original PlayStation 1 (PSn00bSDK)"
)

psn00bsdk_add_executable(fnaf1 GPREL
	src/main.c
	src/game.c
	src/ai.c
	src/video.c
	src/input.c
	src/audio.c
	src/assets.c
	src/ps1_render.c
	src/cd_assets.c
)

target_include_directories(fnaf1 PRIVATE include)

set(TIM_DIR ${PROJECT_SOURCE_DIR}/ps1_assets/tim)
set(VAG_DIR ${PROJECT_SOURCE_DIR}/ps1_assets/vag)

# Minimal embed — cams / office variants / long BGM stream from CD
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_office_39_L  ${TIM_DIR}/office_39_L.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_office_39_R  ${TIM_DIR}/office_39_R.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_menu         ${TIM_DIR}/menu.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_menu2        ${TIM_DIR}/menu2.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_menu3        ${TIM_DIR}/menu3.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_menu4        ${TIM_DIR}/menu4.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_loading      ${TIM_DIR}/loading.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_ui_atlas     ${TIM_DIR}/ui_atlas.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_font_atlas   ${TIM_DIR}/font_atlas.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_door_L       ${TIM_DIR}/door_L.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_door_R       ${TIM_DIR}/door_R.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_bonnie_atlas ${TIM_DIR}/bonnie_atlas.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_chica_atlas  ${TIM_DIR}/chica_atlas.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_freddy_atlas ${TIM_DIR}/freddy_atlas.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_foxy_atlas   ${TIM_DIR}/foxy_atlas.tim)
psn00bsdk_target_incbin(fnaf1 PRIVATE tim_cam_00 ${TIM_DIR}/cam_00_19.tim)

psn00bsdk_target_incbin(fnaf1 PRIVATE vag_blip3           ${VAG_DIR}/blip3.vag)
psn00bsdk_target_incbin(fnaf1 PRIVATE vag_doorclose       ${VAG_DIR}/doorclose.vag)
psn00bsdk_target_incbin(fnaf1 PRIVATE vag_error           ${VAG_DIR}/error.vag)
psn00bsdk_target_incbin(fnaf1 PRIVATE vag_windowscare     ${VAG_DIR}/windowscare.vag)
psn00bsdk_target_incbin(fnaf1 PRIVATE vag_put_down        ${VAG_DIR}/put_down.vag)
psn00bsdk_target_incbin(fnaf1 PRIVATE vag_xscream         ${VAG_DIR}/xscream.vag)
psn00bsdk_target_incbin(fnaf1 PRIVATE vag_static          ${VAG_DIR}/static.vag)
psn00bsdk_target_incbin(fnaf1 PRIVATE vag_deep_steps      ${VAG_DIR}/deep_steps.vag)
psn00bsdk_target_incbin(fnaf1 PRIVATE vag_running_fast3   ${VAG_DIR}/running_fast3.vag)
psn00bsdk_target_incbin(fnaf1 PRIVATE vag_fan_embed       ${VAG_DIR}/fan_embed.vag)
psn00bsdk_target_incbin(fnaf1 PRIVATE vag_menu_embed      ${VAG_DIR}/menu_embed.vag)

psn00bsdk_add_cd_image(
	iso
	fnaf1
	iso.xml
	DEPENDS fnaf1 system.cnf
)
