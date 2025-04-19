@echo off
mkdir .\_unpacked_full
for %%f in (..\..\..\db\*.db*) do (
    echo Unpacking %%f
    converter.exe -unpack -xdb %%f -dir .\_unpacked_full
)
for %%f in (..\..\..\db\textures\*.db*) do (
    echo Unpacking %%f
    converter.exe -unpack -xdb %%f -dir .\_unpacked_full
)
for %%f in (..\..\..\db\patches\*.db*) do (
    echo Unpacking %%f
    converter.exe -unpack -xdb %%f -dir .\_unpacked_full
)
pause