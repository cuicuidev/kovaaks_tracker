const std = @import("std");

const csv = @import("kovaaks_tracker_lib").csv;
const scenario = @import("kovaaks_tracker_lib").scenario;
const http = @import("kovaaks_tracker_lib").http;

const heap = std.heap;
const mem = std.mem;
const fs = std.fs;
const io = std.io;
const os = std.os;
const win32 = os.windows.kernel32;

pub fn main() !void {
    // MEM ALLOCATOR
    var gpa = heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    // STDOUT
    const stdout = io.getStdOut();
    const writer = stdout.writer();

    // PATHS
    const home_env_var_name = "USERPROFILE";
    const home_dir = try std.process.getEnvVarOwned(allocator, home_env_var_name);
    defer allocator.free(home_dir);

    try writer.print("HOME: {s}\n", .{home_dir});

    const config_name = ".kvkstracker\\config.csv";
    const config_path = try std.fmt.allocPrint(allocator, "{s}\\{s}", .{ home_dir, config_name });
    defer allocator.free(config_path);

    try writer.print("Config location: {s}\n", .{config_path});

    const token_name = ".kvkstracker\\access_token.txt";
    const token_path = try std.fmt.allocPrint(allocator, "{s}\\{s}", .{ home_dir, token_name });
    defer allocator.free(token_path);

    try writer.print("Access token location: {s}\n", .{token_path});

    // CONFIG
    var config = try Config.readFrom(
        allocator,
        config_path,
    );
    defer config.deinit();

    // STATS DIR
    var dir = std.fs.openDirAbsolute(
        config.stats_dir,
        .{ .iterate = true },
    ) catch |err| {
        switch (err) {
            error.FileNotFound => {
                try writer.print("error.FileNotFound -> \"{s}\"\n\nPlease reinstall Aimalytics Tracker and specify the correct stats folder path...", .{config.stats_dir});
                std.time.sleep(std.time.ns_per_s * 5);
                return err;
            },
            else => {
                try writer.print("Error: {}\n\nPlease report this issue to support@aimalytics.gg", .{err});
                std.time.sleep(std.time.ns_per_s * 5);
                return err;
            },
        }
    };
    defer dir.close();

    try writer.print("Opened stats dir: {s}\n", .{config.stats_dir});

    // JWT
    const jwt = try readJWT(allocator, token_path);
    defer allocator.free(jwt);

    try writer.print("Access token: {s}\n", .{config.stats_dir});

    // LATEST STAT
    var latest = try http.getLatest(allocator, "https://chubby-krystyna-cuicuidev-da9ab1a9.koyeb.app/latest", jwt, writer);

    try writer.print("Latest timestamp: {}\n", .{latest});

    // WATCHDOG
    while (true) {
        latest = try iterateStatsDir(allocator, dir, latest, jwt, writer);
        std.time.sleep(std.time.ns_per_s * config.time_interval_seconds);
    }
}

/// This function iterates over a dir and sends the payload to the API
pub fn iterateStatsDir(allocator: mem.Allocator, dir: fs.Dir, latest: i128, jwt: []const u8, writer: fs.File.Writer) !i128 {
    var iterator = dir.iterate();
    var highest = latest;
    while (try iterator.next()) |dirContent| {
        var csv_file = try dir.openFile(dirContent.name, .{}); //fs.cwd().openFile(full_path, .{});
        defer csv_file.close();

        const stat = try csv_file.stat();

        if (stat.ctime > latest) {
            var data = try scenario.ScenarioData.fromCsvFile(allocator, csv_file);
            defer data.deinit();

            try http.sendPayload(allocator, &data, "https://chubby-krystyna-cuicuidev-da9ab1a9.koyeb.app/insert", jwt, writer);
            if (stat.ctime > highest) {
                highest = stat.ctime;
            }
        }
    }
    return highest;
}

pub fn readJWT(allocator: mem.Allocator, path: []const u8) ![]u8 {
    const file = try fs.openFileAbsolute(path, .{});
    defer file.close();

    return try file.readToEndAlloc(allocator, 256);
}

const Config = struct {
    allocator: mem.Allocator,
    stats_dir: []const u8,
    time_interval_seconds: u64,

    const Self = @This();

    pub fn deinit(self: *Self) void {
        self.allocator.free(self.stats_dir);
    }

    pub fn readFrom(allocator: mem.Allocator, path: []const u8) !Self {
        const file = try fs.openFileAbsolute(path, .{});
        defer file.close();

        const reader = file.reader();
        var tokenizer = try csv.CsvTokenizer(csv.CsvConfig{ .col_sep = ',', .row_sep = ';', .quotes = '"' }).init(allocator, reader, 512);
        defer tokenizer.deinit();

        var stats_dir: []u8 = undefined;
        var time_interval_seconds: u64 = undefined;

        var next_conf: ?ConfType = null;
        while (try tokenizer.next()) |token| {
            defer token.deinit();

            const token_val = token.value;

            switch (token.token_type) {
                csv.TokenType.FLOAT, csv.TokenType.STRING, csv.TokenType.INT => {
                    if (next_conf) |conf_type| {
                        switch (conf_type) {
                            ConfType.stats_dir => {
                                stats_dir = try allocator.alloc(u8, token_val.len);
                                @memcpy(stats_dir, token_val);
                                next_conf = null;
                            },
                            ConfType.time_interval_seconds => {
                                time_interval_seconds = try std.fmt.parseInt(u64, token_val, 10);
                                next_conf = null;
                            },
                        }
                    } else {
                        if (mem.eql(u8, token_val, "stats_dir")) {
                            next_conf = ConfType.stats_dir;
                        } else if (mem.eql(u8, token_val, "time_interval_seconds")) {
                            next_conf = ConfType.time_interval_seconds;
                        }
                    }
                },
                else => {},
            }
        }

        return .{
            .allocator = allocator,
            .stats_dir = stats_dir,
            .time_interval_seconds = time_interval_seconds,
        };
    }
};

const ConfType = enum {
    time_interval_seconds,
    stats_dir,
};
