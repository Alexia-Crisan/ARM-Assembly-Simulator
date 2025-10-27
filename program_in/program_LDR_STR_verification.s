        ; Test program for LDR and STR (single data transfer)
        ; Verifies:
        ; - LDR/STR basic (no offset)
        ; - LDR/STR with positive offset
        ; - LDR/STR with negative offset
        ; Uses R0–R7, ends with HLT

        MOV     R0, #0x100       ; Base address for data area (in data memory)
        MOV     R1, #10          ; Test value 1
        MOV     R2, #20          ; Test value 2
        MOV     R3, #30          ; Test value 3
        MOV     R4, #40          ; Test value 4

        ; ---------- STORE TESTS ----------
        STR     R1, [R0]         ; Store 10 at [0x100]
        STR     R2, [R0, #4]     ; Store 20 at [0x104]
        STR     R3, [R0, #8]     ; Store 30 at [0x108]
        STR     R4, [R0, #12]    ; Store 40 at [0x10C]

        ; ---------- LOAD TESTS ----------
        LDR     R5, [R0]         ; Load 10 -> R5 = 10
        LDR     R6, [R0, #4]     ; Load 20 -> R6 = 20
        LDR     R7, [R0, #8]     ; Load 30 -> R7 = 30

        ; ---------- OVERWRITE AND RELOAD ----------
        MOV     R3, #99
        STR     R3, [R0, #4]     ; Overwrite memory[0x104] = 99
        LDR     R4, [R0, #4]     ; Load new value -> R4 = 99

        HLT                     ; Stop simulation
