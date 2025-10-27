; Input: N in R0
; Output: sum in R1

MOV R0, #6
MOV R1, #0      ; sum = 0
MOV R2, #1      ; counter = 1

ADD R0, R0, #1

sum_loop:
ADD R1, R1, R2  ; sum += counter
ADD R2, #1  ; counter++

CMP R2, R0      ; compare counter with N
BNE sum_loop     ; if counter < N, loop

STR R1, [R3]
HLT