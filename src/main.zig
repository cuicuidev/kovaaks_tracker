const std = @import("std");

const csv = @import("kovaaks_tracker_lib").csv;
const scenario = @import("kovaaks_tracker_lib").scenario;
const http = @import("kovaaks_tracker_lib").http;

const heap = std.heap;
const mem = std.mem;
const fs = std.fs;
const io = std.io;

const STATS_DIR = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\FPSAimTrainer\\FPSAimTrainer\\stats";

pub fn main() !void {
    var gpa = heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();

    const allocator = gpa.allocator();

    var dir = try std.fs.openDirAbsolute(
        STATS_DIR,
        .{ .iterate = true },
    );
    defer dir.close();

    var iterator = dir.iterate();

    while (try iterator.next()) |dirContent| {
        const file_name = try allocator.alloc(u8, dirContent.name.len);
        @memcpy(file_name, dirContent.name);

        const parts = [_][]const u8{ STATS_DIR, "\\", file_name };
        const full_path = try std.mem.concat(allocator, u8, &parts);
        defer allocator.free(full_path);

        var data = try scenario.ScenarioData.fromCsvFile(allocator, full_path);
        defer data.deinit();
        const payload = try data.jsonSerialize();
        defer allocator.free(payload);
        try http.sendPayload(allocator, payload, "http://127.0.0.1:8000/"); //TODO: all memory leaked if the server returns err
    }
}
