        ; Minimal branch test for all conditions
        MOV     R0, #5          ; Base value
        MOV     R1, #10         ; Comparison value
        MOV     R2, #0          ; Result holder

        ; ---------- Unconditional branch ----------
        B       UNCOND
        MOV     R2, #99         ; skipped
UNCOND:
        MOV     R2, #1          ; R2 = 1 if unconditional branch works

        ; ---------- BEQ / BNE ----------
        CMP     R0, R0          ; equal
        BEQ     BEQ_OK
        MOV     R2, #0
BEQ_OK:
        MOV     R2, #7         

        CMP     R0, R1          ; not equal
        BNE     BNE_OK
        MOV     R2, #0
BNE_OK:
        MOV     R2, #8        

        ; ---------- BLT / BGT ----------
        CMP     R0, R1          ; R0 < R1
        BLT     BLT_OK
        MOV     R2, #0
BLT_OK:
        MOV     R2, #7

        CMP     R1, R0          ; R1 > R0
        BGT     BGT_OK
        MOV     R2, #0
BGT_OK:
        MOV     R2, #8

        ; ---------- BGE / BLE ----------
        CMP     R1, R0          ; R1 > R0
        BGE     BGE_OK
        MOV     R2, #0
BGE_OK:
        MOV     R2, #7

        CMP     R0, R1          ; R0 < R1
        BLE     BLE_OK
        MOV     R2, #0
BLE_OK:
        MOV     R2, #8

        HLT                     ; End program
