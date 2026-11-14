ENTRY(Reset_Handler)

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 112K
    DIAG  (rw)  : ORIGIN = 0x2001C000, LENGTH = 16K
}

__p0_diag_layout = 1;
_estack = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS
{
    .isr_vector :
    {
        . = ALIGN(4);
        KEEP(*(.isr_vector))
        . = ALIGN(4);
    } > FLASH

    .text :
    {
        . = ALIGN(4);
        KEEP(*(.firmware_manifest))
        *(.text*)
        *(.rodata*)
        KEEP(*(.init))
        KEEP(*(.fini))
        . = ALIGN(4);
        _etext = .;
    } > FLASH

    _sidata = LOADADDR(.data);
    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        *(.data*)
        . = ALIGN(4);
        _edata = .;
    } > RAM AT > FLASH

    .bss (NOLOAD) :
    {
        . = ALIGN(4);
        _sbss = .;
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
    } > RAM

    .noinit (NOLOAD) :
    {
        . = ALIGN(4);
        *(.noinit*)
        . = ALIGN(4);
    } > RAM

    .p0_usb_diag (NOLOAD) :
    {
        KEEP(*(.p0_usb_diag))
    } > DIAG
    ASSERT(SIZEOF(.p0_usb_diag) == 15008, "diagnostic journal size")
    ASSERT(ADDR(.p0_usb_diag) == 0x2001C000, "diagnostic journal address")
    ASSERT(_ebss + 8192 < _estack, "diagnostic stack reserve")

    /DISCARD/ :
    {
        *(.comment*)
        *(.note*)
    }
}
