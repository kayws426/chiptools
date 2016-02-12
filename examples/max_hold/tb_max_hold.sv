module tb_max_hold;
    /* ------------------------------------------------------------------------
    ** data_width will be overidden by chiptools, we cannot use parameters
    ** as unfortunately these can not be set by Icarus
    ** ----------------------------------------------------------------------*/
    `ifndef data_width
        `define data_width 3
    `endif
    /* ------------------------------------------------------------------------
    ** Registers / Wires
    ** ----------------------------------------------------------------------*/
    reg clock = 0, reset = 0;
    reg [`data_width-1:0] data;
    wire [`data_width-1:0] max;
    integer fileid;
    integer readCount;
    integer outFileId;
    integer firstCall = 1;
    integer lastCycle = 0;
    reg inReset = 0;
    reg [`data_width-1:0] inData = 0;

    /* ------------------------------------------------------------------------
    ** Open File Handles
    ** ----------------------------------------------------------------------*/
    initial begin
        fileid = $fopen("input.txt", "r");
        outFileId = $fopen("output.txt", "w");
        $display("data_width is%d", `data_width);
        if (fileid == 0) begin
            $display("Could not open file.");
            $finish;
        end
    end

    /* ------------------------------------------------------------------------
    ** Waveform File Dump 
    ** ----------------------------------------------------------------------*/
    initial begin
        $dumpfile("test.vcd");
        $dumpvars(0, tb_max_hold);
    end
    /* ------------------------------------------------------------------------
    ** Clock Generation
    ** Stimulus Generation and Logging
    ** ----------------------------------------------------------------------*/
    always begin
        #5 clock = !clock;
    end
    always begin
        if (!lastCycle) begin
            $fscanf(fileid, "%b %b\n", inReset, inData);
        end
        reset <= inReset;
        data <= inData;
        @(posedge clock);
        if (firstCall) begin
            firstCall = 0;
        end else begin
            if (!lastCycle) begin
                $fwrite(outFileId, "%b\n", max);
                if ($feof(fileid)) begin
                    $fclose(fileid);
                    lastCycle = 1;
                end
            end else begin
                $fwrite(outFileId, "%b\n", max);
                $fflush();
                $fclose(outFileId);
                $finish;
            end
        end
    end

    /* ------------------------------------------------------------------------
    ** UUT Instance
    ** ----------------------------------------------------------------------*/
    max_hold #(.data_width(`data_width)) uut (clock, reset, data, max);

endmodule
