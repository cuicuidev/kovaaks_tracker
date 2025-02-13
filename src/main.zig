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

    const latest = try http.getLatest(allocator, "http://127.0.0.1:8000/latest");

    while (try iterator.next()) |dirContent| {
        const parts = [_][]const u8{ STATS_DIR, "\\", dirContent.name };
        const full_path = try std.mem.concat(allocator, u8, &parts);
        defer allocator.free(full_path);

        var csv_file = try fs.cwd().openFile(full_path, .{});
        defer csv_file.close();

        const stat = try csv_file.stat();

        if (stat.ctime > latest) {
            std.debug.print("Stat:\n{}\t{}\n\n", .{ stat.ctime, latest });

            var data = try scenario.ScenarioData.fromCsvFile(allocator, full_path);
            defer data.deinit();

            const payload = try data.jsonSerialize();
            defer allocator.free(payload);

            std.debug.print("Payload:\n{s}\n\n", .{payload});

            try http.sendPayload(allocator, payload, "http://127.0.0.1:8000/insert");
        }
    }
}

pub fn startup() !void {}
