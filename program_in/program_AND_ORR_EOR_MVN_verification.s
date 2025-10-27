        ; ============================================================
        ; Test program for AND, SUB, ORR, EOR, MVN (2- and 3-operand forms)
        ; Uses R0–R12
        ; Ends with HLT (halt simulation)
        ; ============================================================

        MOV     R0, #0x0F        ; 00001111b (15)
        MOV     R1, #0xF0        ; 11110000b (240)
        MOV     R2, #0x55        ; 01010101b (85)
        MOV     R3, #0xAA        ; 10101010b (170)
        MOV     R4, #1           ; constant 1

        ; ---------- AND ----------
        AND     R5, R0, R1       ; 00001111 AND 11110000 = 00000000 (0x00)
        AND     R6, R2, R3       ; 01010101 AND 10101010 = 00000000 (0x00)
        AND     R7, R0, #0x0A    ; 00001111 AND 00001010 = 00001010 (0x0A)
        AND     R5, R1           ; 00000000 AND 11110000 = 00000000 (0x00)
        AND     R6, #0xFF        ; 00000000 AND 11111111 = 00000000 (0x00)

        ; ---------- ORR ----------
        ORR     R0, R2, R3       ; 01010101 OR 10101010 = 11111111 (0xFF)
        ORR     R1, R0, #0x80    ; 11111111 OR 10000000 = 11111111 (0xFF)
        ORR     R2, R0           ; 01010101 OR 11111111 = 11111111 (0xFF)
        ORR     R3, #0x0F        ; 10101010 OR 00001111 = 10101111 (0xAF)

        ; ---------- EOR ----------
        EOR     R4, R2, R3       ; 11111111 XOR 10101111 = 01010000 (0x50)
        EOR     R5, R4, #0xAA    ; 01010000 XOR 10101010 = 11111010 (0xFA)
        EOR     R6, R5           ; 00000000 XOR 11111010 = 11111010 (0xFA)
        EOR     R7, #0xFF        ; 00001010 XOR 11111111 = 11110101 (0xF5)

        ; ---------- MVN ----------
        MVN R11, R0
        MVN R12, #10

        ; ---------- Combined test ----------
        AND     R8, R9, R6       ; Bitwise AND
        EOR     R8, R8, #0x0F    ; XOR result with 0x0F
        ORR     R10, R8, R7      ; Combine result via OR
  
        ; ---------- End of program ----------
        HLT                     ; Stop simulation
